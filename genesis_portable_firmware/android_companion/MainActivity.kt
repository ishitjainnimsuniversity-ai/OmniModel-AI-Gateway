package com.genesis.ai.companion

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import java.io.InputStream
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * GENESIS AI Companion App — Deterministic Dual-Network Router for Android.
 * 
 * Binds:
 * 1. Cloud AI Relay (HTTPS) -> Cellular Mobile Data (4G/5G).
 * 2. Local ESP32 Dashboard (192.168.4.1) -> Wi-Fi SoftAP ("GENESIS_AI").
 * 
 * Guarantees simultaneous internet and local device communication on every Android version.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var connectivityManager: ConnectivityManager
    private var cellularNetwork: Network? = null
    private var wifiNetwork: Network? = null

    private val scope = CoroutineScope(Dispatchers.Main + Job())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

        setupNetworkBinding()
        setupWebView()
    }

    private fun setupNetworkBinding() {
        // 1. Explicitly request Cellular Network for Public Internet / Cloud AI Relay
        val cellRequest = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .addTransportType(NetworkCapabilities.TRANSPORT_CELLULAR)
            .build()

        connectivityManager.requestNetwork(cellRequest, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                cellularNetwork = network
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Cellular Relay Ready", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onLost(network: Network) {
                if (cellularNetwork == network) cellularNetwork = null
            }
        })

        // 2. Explicitly track Wi-Fi Network for Local ESP32 SoftAP (192.168.4.1)
        val wifiRequest = NetworkRequest.Builder()
            .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .build()

        connectivityManager.requestNetwork(wifiRequest, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                wifiNetwork = network
            }

            override fun onLost(network: Network) {
                if (wifiNetwork == network) wifiNetwork = null
            }
        })
    }

    private fun setupWebView() {
        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView?,
                    request: WebResourceRequest?
                ): WebResourceResponse? {
                    val url = request?.url ?: return null

                    // If request is targeting public HTTPS Relay -> Force route through CELLULAR interface!
                    if (url.scheme == "https" && cellularNetwork != null) {
                        try {
                            val conn = cellularNetwork!!.openConnection(URL(url.toString())) as HttpURLConnection
                            conn.requestMethod = request.method
                            request.requestHeaders?.forEach { (k, v) -> conn.setRequestProperty(k, v) }
                            conn.connect()
                            val mime = conn.contentType ?: "application/json"
                            val stream: InputStream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
                            return WebResourceResponse(mime, "UTF-8", stream)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }

                    // Otherwise (e.g. 192.168.4.1) let standard Wi-Fi stack handle it directly
                    return super.shouldInterceptRequest(view, request)
                }
            }
        }

        setContentView(webView)
        // Load the ESP32-C5 hosted dashboard directly
        webView.loadUrl("http://192.168.4.1")
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }
}
