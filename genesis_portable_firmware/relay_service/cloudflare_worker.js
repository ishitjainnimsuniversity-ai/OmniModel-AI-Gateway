/**
 * GENESIS AI — Secure Serverless HTTPS AI Relay Service
 * Deployable to Cloudflare Workers, Vercel Edge Functions, or Node.js.
 * 
 * SECURITY:
 * Provider API keys (GEMINI_API_KEY) live EXCLUSIVELY in server environment variables.
 * Keys are NEVER transmitted to the browser, ESP32, or logged.
 */

export default {
  async fetch(request, env) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-Id",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Health check endpoint
    if (url.pathname === "/health" || url.pathname === "/api/health") {
      return new Response(JSON.stringify({
        status: "ok",
        service: "GENESIS AI Cloud Relay",
        provider: "gemini+flux",
        models: ["gemini-2.5-flash", "gemini-2.5-pro", "flux.1-schnell"]
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // Multimodal Image Generation Endpoint
    if (url.pathname === "/api/image/generate" && request.method === "POST") {
      try {
        const body = await request.json();
        const prompt = (body.prompt || "").trim();
        const style = body.style || "Photorealistic";
        const aspect = body.aspect_ratio || "1:1";
        const requestId = body.request_id || ("img_" + Math.random().toString(36).substring(2, 10));

        if (!prompt) {
          return new Response(JSON.stringify({ error: "Empty image prompt" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const dims = {
          "1:1": [512, 512],
          "16:9": [768, 432],
          "9:16": [432, 768],
          "4:3": [640, 480],
          "3:4": [480, 640]
        }[aspect] || [512, 512];

        const stylePrompts = {
          "Photorealistic": "photorealistic, 8k raw photography, hyper-detailed, studio lighting",
          "Anime / Manga": "anime aesthetic, clean linework, vibrant makoto shinkai style, illustration",
          "Cyberpunk": "cyberpunk style, neon lights, rainy reflections, futuristic cityscape, octane render",
          "Cinematic": "cinematic film still, 35mm photograph, dramatic movie lighting",
          "Digital Art": "digital art masterpiece, trending on artstation, intricate concept art",
          "Dark Fantasy": "dark fantasy, dramatic shadows, mysterious glowing runes, fog, unreal engine 5",
          "Watercolor": "delicate watercolor painting, artistic pigment bleeding, textured paper",
          "3D Render": "3d octane render, ray tracing, smooth textures, subsurface scattering, 8k cgi"
        };

        const mod = stylePrompts[style] || "";
        const fullPrompt = mod ? `${prompt}, ${mod}` : prompt;
        const seed = Math.floor(Math.random() * 999999);
        const genUrl = `https://image.pollinations.ai/prompt/${encodeURIComponent(fullPrompt)}?width=${dims[0]}&height=${dims[1]}&seed=${seed}&model=flux&nologo=true`;

        const upstreamResp = await fetch(genUrl);
        if (!upstreamResp.ok) {
          return new Response(JSON.stringify({ error: `Image provider HTTP ${upstreamResp.status}` }), {
            status: upstreamResp.status,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const imageBuffer = await upstreamResp.arrayBuffer();
        let binary = "";
        const bytes = new Uint8Array(imageBuffer);
        for (let i = 0; i < bytes.byteLength; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const b64 = btoa(binary);

        return new Response(JSON.stringify({
          ok: true,
          request_id: requestId,
          image_url: `data:image/jpeg;base64,${b64}`,
          prompt: prompt,
          style: style,
          aspect_ratio: aspect,
          width: dims[0],
          height: dims[1]
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    // AI Generation Chat Endpoint
    if (url.pathname === "/api/chat" && request.method === "POST") {
      try {
        const body = await request.json();
        const message = (body.message || "").trim();
        const model = body.model || "gemini-2.5-flash";
        const requestId = body.request_id || ("req_" + Math.random().toString(36).substring(2, 10));

        if (!message) {
          return new Response(JSON.stringify({ error: "Empty prompt" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const apiKey = env.GEMINI_API_KEY;
        if (!apiKey) {
          return new Response(JSON.stringify({ error: "Relay GEMINI_API_KEY is not configured" }), {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        // Call Google Gemini API with Server-Sent Events (SSE) streaming
        const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${model}:streamGenerateContent?alt=sse&key=${apiKey}`;

        const geminiPayload = {
          contents: [
            {
              role: "user",
              parts: [{ text: message }]
            }
          ],
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 2048
          }
        };

        const geminiResp = await fetch(geminiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(geminiPayload)
        });

        if (!geminiResp.ok) {
          const errDetail = await geminiResp.text();
          return new Response(JSON.stringify({
            error: `Gemini API error (${geminiResp.status}): ${errDetail.substring(0, 160)}`
          }), {
            status: geminiResp.status,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        // Transform upstream SSE stream to relay client format
        const { readable, writable } = new TransformStream();
        const writer = writable.getWriter();
        const encoder = new TextEncoder();

        (async () => {
          const reader = geminiResp.body.getReader();
          const decoder = new TextDecoder();
          let buf = "";

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              buf += decoder.decode(value, { stream: true });
              const lines = buf.split("\n");
              buf = lines.pop();

              for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const jsonStr = line.substring(5).trim();
                try {
                  const data = JSON.parse(jsonStr);
                  const candidate = (data.candidates || [])[0];
                  const text = (candidate?.content?.parts || []).map(p => p.text).join("");
                  if (text) {
                    await writer.write(encoder.encode(`data: ${JSON.stringify({ delta: text })}\n\n`));
                  }
                } catch (e) {}
              }
            }
            await writer.write(encoder.encode("data: [DONE]\n\n"));
          } catch (streamErr) {
            await writer.write(encoder.encode(`data: ${JSON.stringify({ error: streamErr.message })}\n\n`));
          } finally {
            await writer.close();
          }
        })();

        return new Response(readable, {
          headers: {
            ...corsHeaders,
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
          }
        });

      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Not Found", { status: 404, headers: corsHeaders });
  }
};
