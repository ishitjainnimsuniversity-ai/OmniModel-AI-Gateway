#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ArduinoJson.h>

WebServer server(80);
DNSServer dnsServer;

void setup() {
    Serial.begin(115200);
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
    WiFi.softAP("GENESIS_AI");
    dnsServer.start(53, "*", IPAddress(192, 168, 4, 1));
    server.on("/", []() {
        server.send(200, "text/html", "<h1>GENESIS AI SoftAP</h1>");
    });
    server.begin();
}

void loop() {
    dnsServer.processNextRequest();
    server.handleClient();
}
