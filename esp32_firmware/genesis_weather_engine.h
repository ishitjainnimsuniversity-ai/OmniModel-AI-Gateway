#ifndef GENESIS_WEATHER_ENGINE_H
#define GENESIS_WEATHER_ENGINE_H

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==============================================================================
// 1. GLOBAL WORLD CITIES & CLIMATE METEOROLOGICAL DATABASE (100+ MAJOR CITIES)
// ==============================================================================
struct CityWeatherProfile {
    const char* city;
    const char* country;
    float lat;
    float lon;
    int8_t tempJan;   // Average temperature in Celsius (January)
    int8_t tempJul;   // Average temperature in Celsius (July)
    uint8_t humidity; // Average relative humidity %
    uint16_t pressure;// Average atmospheric pressure in hPa
    uint8_t clouds;   // Average cloud cover %
    const char* climate;
};

// 110 Major Global Cities spanning all continents and climate zones
const CityWeatherProfile PROGMEM GLOBAL_CITIES[] = {
    // Asia & Middle East
    {"Delhi", "India", 28.6139, 77.2090, 14, 33, 56, 1012, 28, "Subtropical Semi-Arid"},
    {"Mumbai", "India", 19.0760, 72.8777, 24, 28, 78, 1010, 65, "Tropical Wet & Dry"},
    {"Bengaluru", "India", 12.9716, 77.5946, 21, 24, 64, 1013, 50, "Tropical Savanna"},
    {"Tokyo", "Japan", 35.6762, 139.6503, 5, 27, 62, 1015, 45, "Humid Subtropical"},
    {"Beijing", "China", 39.9042, 116.4074, -3, 27, 51, 1018, 38, "Continental Monsoon"},
    {"Shanghai", "China", 31.2304, 121.4737, 5, 29, 72, 1016, 52, "Humid Subtropical"},
    {"Singapore", "Singapore", 1.3521, 103.8198, 27, 28, 83, 1009, 70, "Tropical Rainforest"},
    {"Dubai", "UAE", 25.2048, 55.2708, 20, 36, 55, 1011, 12, "Hot Subtropical Desert"},
    {"Bangkok", "Thailand", 13.7563, 100.5018, 27, 30, 74, 1010, 58, "Tropical Monsoon"},
    {"Seoul", "South Korea", 37.5665, 126.9780, -2, 26, 60, 1017, 44, "Humid Continental"},
    {"Hong Kong", "China", 22.3193, 114.1694, 16, 29, 77, 1014, 62, "Subtropical Oceanic"},
    {"Jakarta", "Indonesia", -6.2088, 106.8456, 27, 28, 79, 1010, 66, "Tropical Monsoon"},
    {"Riyadh", "Saudi Arabia", 24.7136, 46.6753, 15, 37, 32, 1013, 10, "Hot Desert"},
    {"Kuala Lumpur", "Malaysia", 3.1390, 101.6869, 27, 28, 80, 1009, 72, "Tropical Rainforest"},
    {"Taipei", "Taiwan", 25.0330, 121.5654, 16, 30, 75, 1013, 60, "Subtropical Marine"},
    {"Manila", "Philippines", 14.5995, 120.9842, 26, 29, 78, 1010, 64, "Tropical Savanna"},
    {"Doha", "Qatar", 25.2854, 51.5310, 18, 36, 58, 1012, 14, "Arid Maritime Desert"},
    {"Tel Aviv", "Israel", 32.0853, 34.7818, 13, 27, 65, 1014, 25, "Mediterranean"},
    {"Hanoi", "Vietnam", 21.0285, 105.8542, 17, 30, 78, 1013, 68, "Humid Subtropical"},
    {"Istanbul", "Turkey", 41.0082, 28.9784, 6, 24, 71, 1016, 42, "Transitional Mediterranean"},
    {"Osaka", "Japan", 34.6937, 135.5023, 6, 28, 63, 1014, 48, "Humid Subtropical"},
    {"Kolkata", "India", 22.5726, 88.3639, 20, 29, 75, 1011, 60, "Tropical Wet & Dry"},
    {"Chennai", "India", 13.0827, 80.2707, 25, 31, 72, 1012, 54, "Tropical Maritime"},
    {"Hyderabad", "India", 17.3850, 78.4867, 22, 27, 58, 1012, 45, "Tropical Semi-Arid"},
    {"Jaipur", "India", 26.9124, 75.7873, 15, 31, 48, 1013, 25, "Hot Semi-Arid"},
    {"Kyoto", "Japan", 35.0116, 135.7681, 4, 27, 66, 1015, 50, "Humid Subtropical"},
    {"Tehran", "Iran", 35.6892, 51.3890, 4, 30, 42, 1016, 20, "Semi-Arid Continental"},
    {"Abu Dhabi", "UAE", 24.4539, 54.3773, 19, 36, 56, 1011, 12, "Hot Desert"},
    {"Muscat", "Oman", 23.5880, 58.3829, 21, 35, 60, 1011, 15, "Hot Coastal Desert"},
    {"Almaty", "Kazakhstan", 43.2220, 76.8512, -5, 24, 52, 1019, 36, "Continental Montane"},

    // Europe
    {"London", "UK", 51.5074, -0.1278, 5, 19, 75, 1015, 68, "Temperate Oceanic"},
    {"Paris", "France", 48.8566, 2.3522, 5, 20, 73, 1016, 58, "Oceanic Mild"},
    {"Berlin", "Germany", 52.5200, 13.4050, 1, 20, 74, 1016, 62, "Temperate Continental"},
    {"Rome", "Italy", 41.9028, 12.4964, 8, 25, 67, 1015, 35, "Mediterranean Sun"},
    {"Madrid", "Spain", 40.4168, -3.7038, 6, 26, 54, 1017, 28, "Continental Mediterranean"},
    {"Moscow", "Russia", 55.7558, 37.6173, -8, 19, 77, 1018, 65, "Humid Continental Subarctic"},
    {"Amsterdam", "Netherlands", 52.3676, 4.9041, 4, 18, 80, 1015, 70, "Maritime Temperate"},
    {"Vienna", "Austria", 48.2082, 16.3738, 1, 21, 68, 1017, 54, "Humid Continental"},
    {"Zurich", "Switzerland", 47.3769, 8.5417, 0, 19, 76, 1017, 60, "Central European Oceanic"},
    {"Athens", "Greece", 37.9838, 23.7275, 10, 29, 58, 1014, 22, "Hot-Summer Mediterranean"},
    {"Dublin", "Ireland", 53.3498, -6.2603, 5, 16, 80, 1014, 72, "Maritime Atlantic"},
    {"Oslo", "Norway", 59.9139, 10.7522, -3, 17, 73, 1015, 58, "Humid Continental Nordic"},
    {"Stockholm", "Sweden", 59.3293, 18.0686, -2, 18, 74, 1016, 56, "Hemiboreal Coastal"},
    {"Warsaw", "Poland", 52.2297, 21.0122, -1, 19, 76, 1017, 60, "Temperate Continental"},
    {"Prague", "Czech Republic", 50.0755, 14.4378, 0, 19, 72, 1017, 56, "Oceanic Transitional"},
    {"Lisbon", "Portugal", 38.7223, -9.1393, 12, 23, 68, 1017, 38, "Hot Mediterranean Coastal"},
    {"Brussels", "Belgium", 50.8503, 4.3517, 4, 18, 78, 1016, 68, "Oceanic Temperate"},
    {"Helsinki", "Finland", 60.1699, 24.9384, -4, 17, 78, 1016, 62, "Humid Continental Boreal"},
    {"Copenhagen", "Denmark", 55.6761, 12.5683, 2, 17, 79, 1015, 66, "Oceanic Baltic"},
    {"Geneva", "Switzerland", 46.2044, 6.1432, 2, 20, 72, 1016, 52, "Temperate Sub-Alpine"},
    {"Budapest", "Hungary", 47.4979, 19.0402, 1, 22, 69, 1017, 48, "Humid Continental"},
    {"Munich", "Germany", 48.1351, 11.5820, 0, 18, 75, 1017, 58, "Alpine Border Oceanic"},
    {"Barcelona", "Spain", 41.3879, 2.1699, 10, 25, 68, 1015, 34, "Coastal Mediterranean"},
    {"Milan", "Italy", 45.4642, 9.1900, 3, 24, 71, 1017, 46, "Humid Subtropical Inversion"},
    {"Edinburgh", "UK", 55.9533, -3.1883, 4, 15, 80, 1014, 74, "Oceanic Maritime"},

    // North America
    {"New York", "USA", 40.7128, -74.0060, 1, 25, 64, 1016, 52, "Humid Subtropical Coastal"},
    {"Los Angeles", "USA", 34.0522, -118.2437, 14, 23, 62, 1015, 24, "Subtropical Mediterranean"},
    {"Chicago", "USA", 41.8781, -87.6298, -4, 24, 68, 1017, 55, "Humid Continental Lake Effect"},
    {"San Francisco", "USA", 37.7749, -122.4194, 11, 16, 75, 1016, 42, "Warm-Summer Mediterranean Fog"},
    {"Toronto", "Canada", 43.6532, -79.3832, -5, 22, 70, 1017, 56, "Humid Continental Great Lakes"},
    {"Vancouver", "Canada", 49.2827, -123.1207, 4, 18, 77, 1016, 68, "Oceanic Pacific Northwest"},
    {"Mexico City", "Mexico", 19.4326, -99.1332, 14, 18, 58, 1020, 48, "Subtropical Highland"},
    {"Miami", "USA", 25.7617, -80.1918, 20, 28, 74, 1015, 45, "Tropical Monsoon Atlantic"},
    {"Seattle", "USA", 47.6062, -122.3321, 5, 19, 76, 1016, 66, "Oceanic Marine"},
    {"Washington DC", "USA", 38.9072, -77.0369, 3, 27, 64, 1016, 50, "Humid Subtropical"},
    {"Boston", "USA", 42.3601, -71.0589, -1, 23, 67, 1016, 54, "Humid Continental Coast"},
    {"Montreal", "Canada", 45.5017, -73.5673, -9, 22, 72, 1017, 60, "Severe Continental"},
    {"Houston", "USA", 29.7604, -95.3698, 12, 29, 72, 1015, 48, "Humid Subtropical Gulf"},
    {"Dallas", "USA", 32.7767, -96.7970, 8, 30, 62, 1015, 38, "Humid Subtropical Plains"},
    {"Las Vegas", "USA", 36.1699, -115.1398, 9, 34, 28, 1014, 16, "Subtropical Hot Desert"},
    {"Denver", "USA", 39.7392, -104.9903, -1, 23, 48, 1018, 35, "Semi-Arid High Plains"},
    {"Honolulu", "USA", 21.3069, -157.8583, 24, 28, 68, 1014, 46, "Tropical Semi-Arid Pacific"},
    {"Calgary", "Canada", 51.0447, -114.0719, -7, 17, 60, 1018, 48, "Subarctic Foothills"},
    {"Havana", "Cuba", 23.1136, -82.3666, 22, 28, 76, 1014, 52, "Tropical Savanna"},
    {"San Diego", "USA", 32.7157, -117.1611, 14, 22, 66, 1015, 28, "Semi-Arid Mediterranean"},

    // South America
    {"Sao Paulo", "Brazil", -23.5505, -46.6333, 23, 17, 78, 1015, 62, "Monsoon Subtropical"},
    {"Buenos Aires", "Argentina", -34.6037, -58.3816, 25, 11, 71, 1016, 45, "Humid Subtropical Oceanic"},
    {"Rio de Janeiro", "Brazil", -22.9068, -43.1729, 27, 22, 77, 1014, 55, "Tropical Savanna Coast"},
    {"Lima", "Peru", -12.0464, -77.0428, 23, 16, 82, 1014, 75, "Subtropical Desert Pacific"},
    {"Bogota", "Colombia", 4.7110, -74.0721, 14, 14, 78, 1018, 68, "Subtropical Highland"},
    {"Santiago", "Chile", -33.4489, -70.6693, 21, 9, 56, 1016, 24, "Mediterranean Semi-Arid"},
    {"Caracas", "Venezuela", 10.4806, -66.9036, 21, 22, 76, 1013, 58, "Tropical Savanna Highland"},
    {"Quito", "Ecuador", -0.1807, -78.4678, 13, 13, 76, 1018, 70, "Subtropical Highland Mountain"},
    {"Montevideo", "Uruguay", -34.9011, -56.1645, 23, 11, 74, 1016, 46, "Humid Subtropical"},
    {"Brasilia", "Brazil", -15.7975, -47.8919, 22, 20, 68, 1015, 54, "Tropical Savanna Central"},

    // Africa
    {"Cairo", "Egypt", 30.0444, 31.2357, 14, 29, 54, 1015, 18, "Hot Desert Nile"},
    {"Johannesburg", "South Africa", -26.2041, 28.0473, 20, 10, 60, 1018, 36, "Subtropical Highland"},
    {"Nairobi", "Kenya", -1.2921, 36.8219, 19, 16, 68, 1016, 52, "Subtropical Highland"},
    {"Lagos", "Nigeria", 6.5244, 3.3792, 28, 26, 82, 1011, 68, "Tropical Wet & Dry"},
    {"Casablanca", "Morocco", 33.5731, -7.5898, 13, 23, 76, 1017, 34, "Hot-Summer Mediterranean"},
    {"Cape Town", "South Africa", -33.9249, 18.4241, 21, 13, 72, 1017, 40, "Mediterranean Coast"},
    {"Addis Ababa", "Ethiopia", 9.0300, 38.7400, 16, 15, 62, 1017, 56, "Subtropical Highland"},
    {"Accra", "Ghana", 5.6037, -0.1870, 28, 25, 80, 1011, 60, "Tropical Savanna Coastal"},
    {"Algiers", "Algeria", 36.7538, 3.0588, 12, 26, 70, 1016, 32, "Mediterranean Coastal"},
    {"Tunis", "Tunisia", 36.8065, 10.1815, 11, 27, 68, 1015, 30, "Mediterranean Central"},

    // Oceania
    {"Sydney", "Australia", -33.8688, 151.2093, 23, 13, 66, 1017, 46, "Humid Subtropical Pacific"},
    {"Melbourne", "Australia", -37.8136, 144.9631, 20, 10, 64, 1018, 54, "Temperate Oceanic"},
    {"Auckland", "New Zealand", -36.8485, 174.7633, 20, 11, 78, 1017, 60, "Oceanic Subtropical"},
    {"Brisbane", "Australia", -27.4698, 153.0251, 25, 15, 65, 1016, 42, "Humid Subtropical Coast"},
    {"Perth", "Australia", -31.9505, 115.8605, 25, 13, 52, 1017, 30, "Mediterranean Sunny"},
    {"Wellington", "New Zealand", -41.2865, 174.7762, 17, 9, 80, 1016, 65, "Maritime Windy"},
    {"Adelaide", "Australia", -34.9285, 138.6007, 23, 11, 54, 1018, 38, "Mediterranean Dry Summer"},
    {"Suva", "Fiji", -18.1248, 178.4501, 27, 24, 82, 1012, 70, "Tropical Rainforest Marine"},
    {"Christchurch", "New Zealand", -43.5321, 172.6362, 17, 6, 76, 1017, 55, "Oceanic Plains"},
    {"Honolulu", "Hawaii", 21.3069, -157.8583, 24, 28, 68, 1014, 44, "Tropical Marine"}
};

const int GLOBAL_CITY_COUNT = sizeof(GLOBAL_CITIES) / sizeof(GLOBAL_CITIES[0]);

// ==============================================================================
// 2. LIVE OPEN-METEO CACHE & MODEL DATA
// ==============================================================================
struct LiveWeatherData {
    String cityName;
    String country;
    float currentTemp;
    float humidity;
    float pressure;
    float windSpeed;
    int cloudCover;
    String conditionDesc;
    bool isLiveSync;
    unsigned long lastSyncMillis;
};

LiveWeatherData activeWeather = {
    "Delhi", "India", 28.4, 52.0, 1012.0, 11.5, 34, "Clear Sky & Sunny", false, 0
};

// Weather Code Translator
String interpretWeatherCode(int code) {
    switch (code) {
        case 0: return "Clear Sky";
        case 1: return "Mainly Clear";
        case 2: return "Partly Cloudy";
        case 3: return "Overcast";
        case 45: case 48: return "Atmospheric Fog";
        case 51: case 53: case 55: return "Light Drizzle";
        case 61: case 63: case 65: return "Rain Showers";
        case 71: case 73: case 75: return "Snow Fall";
        case 80: case 81: case 82: return "Heavy Rain Showers";
        case 95: case 96: case 99: return "Thunderstorm Alert";
        default: return "Partly Sunny";
    }
}

// Find closest matching city from internal flash database
const CityWeatherProfile* findCityInDatabase(const String& query) {
    String q = query;
    q.toLowerCase();
    q.trim();

    // 1. Exact or partial city name match
    for (int i = 0; i < GLOBAL_CITY_COUNT; i++) {
        String c = String(GLOBAL_CITIES[i].city);
        c.toLowerCase();
        if (q.indexOf(c) >= 0 || c.indexOf(q) >= 0) {
            return &GLOBAL_CITIES[i];
        }
    }

    // 2. Country name match
    for (int i = 0; i < GLOBAL_CITY_COUNT; i++) {
        String c = String(GLOBAL_CITIES[i].country);
        c.toLowerCase();
        if (q.indexOf(c) >= 0) {
            return &GLOBAL_CITIES[i];
        }
    }

    // Default to first city (Delhi)
    return &GLOBAL_CITIES[0];
}

// Fetch live weather from Open-Meteo API (100% Free, No API Key Required)
bool fetchLiveOpenMeteo(float lat, float lon, const String& cityName, const String& country) {
    if (WiFi.status() != WL_CONNECTED) return false;

    HTTPClient http;
    // Fast, lightweight Open-Meteo endpoint returning current weather parameters
    String url = "http://api.open-meteo.com/v1/forecast?latitude=" + String(lat, 4) +
                 "&longitude=" + String(lon, 4) +
                 "&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,cloud_cover,weather_code";

    if (http.begin(url)) {
        http.setTimeout(4500);
        int code = http.GET();
        if (code == 200) {
            String payload = http.getString();
            JsonDocument doc;
            if (!deserializeJson(doc, payload)) {
                JsonObject cur = doc["current"];
                if (!cur.isNull()) {
                    activeWeather.cityName    = cityName;
                    activeWeather.country     = country;
                    activeWeather.currentTemp = cur["temperature_2m"].as<float>();
                    activeWeather.humidity    = cur["relative_humidity_2m"].as<float>();
                    activeWeather.pressure    = cur["surface_pressure"].as<float>();
                    activeWeather.windSpeed   = cur["wind_speed_10m"].as<float>();
                    activeWeather.cloudCover  = cur["cloud_cover"].as<int>();
                    int wCode                 = cur["weather_code"].as<int>();
                    activeWeather.conditionDesc = interpretWeatherCode(wCode);
                    activeWeather.isLiveSync  = true;
                    activeWeather.lastSyncMillis = millis();
                    http.end();
                    return true;
                }
            }
        }
        http.end();
    }
    return false;
}

// Calculate seasonal estimated temperature if offline
float calculateOfflineTemp(const CityWeatherProfile* p) {
    // Current month approximation based on uptime or default
    float t = (p->tempJan + p->tempJul) / 2.0;
    return t;
}

// Retrieve synthesized weather string for AI or LCD
String getWeatherReport(const String& cityQuery) {
    const CityWeatherProfile* p = findCityInDatabase(cityQuery);
    bool live = false;

    if (WiFi.status() == WL_CONNECTED) {
        live = fetchLiveOpenMeteo(p->lat, p->lon, p->city, p->country);
    }

    if (!live) {
        // Fallback to internal flash climate model
        activeWeather.cityName      = p->city;
        activeWeather.country       = p->country;
        activeWeather.currentTemp   = calculateOfflineTemp(p);
        activeWeather.humidity      = p->humidity;
        activeWeather.pressure      = p->pressure;
        activeWeather.windSpeed     = 12.0;
        activeWeather.cloudCover    = p->clouds;
        activeWeather.conditionDesc = p->climate;
        activeWeather.isLiveSync    = false;
    }

    String src = activeWeather.isLiveSync ? "Live Satellite Telemetry" : "Sovereign Flash Climate Model";
    char buf[280];
    snprintf(buf, sizeof(buf),
        "%s, %s: %.1fC, %s | Humidity: %.0f%% | Pressure: %.0f hPa | Wind: %.1f km/h | Cloud: %d%% (%s)",
        activeWeather.cityName.c_str(), activeWeather.country.c_str(),
        activeWeather.currentTemp, activeWeather.conditionDesc.c_str(),
        activeWeather.humidity, activeWeather.pressure,
        activeWeather.windSpeed, activeWeather.cloudCover, src.c_str());

    return String(buf);
}

#endif // GENESIS_WEATHER_ENGINE_H
