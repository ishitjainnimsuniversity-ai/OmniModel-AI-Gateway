#ifndef GENESIS_MEMORY_ENGINE_H
#define GENESIS_MEMORY_ENGINE_H

#include <Arduino.h>
#include <Preferences.h>

// ==============================================================================
// GENESIS AI 5.0 - PERSISTENT NVS KNOWLEDGE & MEMORY ENGINE
// ==============================================================================
// Allows feeding facts, preferences, documents, and notes permanently into
// on-chip flash memory that persists across reboots, power cuts, and updates.
// ==============================================================================

#define MAX_MEMORY_SLOTS 20
Preferences memPrefs;

void initMemoryEngine() {
    memPrefs.begin("genesis_mem", false);
}

int getMemoryCount() {
    return memPrefs.getUInt("count", 0);
}

bool feedKnowledge(const String& fact) {
    String cleanFact = fact;
    cleanFact.trim();
    if (cleanFact.length() < 2) return false;

    int count = getMemoryCount();
    if (count >= MAX_MEMORY_SLOTS) {
        // Shift old memories to make room for newest
        for (int i = 0; i < MAX_MEMORY_SLOTS - 1; i++) {
            String next = memPrefs.getString(String("m_" + String(i + 1)).c_str(), "");
            memPrefs.putString(String("m_" + String(i)).c_str(), next);
        }
        count = MAX_MEMORY_SLOTS - 1;
    }

    String key = "m_" + String(count);
    memPrefs.putString(key.c_str(), cleanFact);
    memPrefs.putUInt("count", count + 1);
    return true;
}

String recallAllKnowledge() {
    int count = getMemoryCount();
    if (count == 0) {
        return "Memory bank is currently empty. You can feed facts anytime by saying 'Remember that [fact]' or using the Memory Feed panel.";
    }

    String res = "GENESIS AI 5.0 Stored Knowledge (" + String(count) + " facts):\n";
    for (int i = 0; i < count; i++) {
        String key = "m_" + String(i);
        String fact = memPrefs.getString(key.c_str(), "");
        if (fact.length() > 0) {
            res += String(i + 1) + ". " + fact + "\n";
        }
    }
    return res;
}

String getMemoryContextString() {
    int count = getMemoryCount();
    if (count == 0) return "";

    String ctx = " [Stored Memory: ";
    for (int i = 0; i < count; i++) {
        String key = "m_" + String(i);
        String fact = memPrefs.getString(key.c_str(), "");
        if (fact.length() > 0) {
            ctx += "(" + fact + ") ";
        }
    }
    ctx += "] ";
    return ctx;
}

void clearAllKnowledge() {
    memPrefs.clear();
    memPrefs.putUInt("count", 0);
}

// Automatic Natural Language Fact Extraction
bool checkAndProcessFeeding(const String& prompt, String& reply) {
    String p = prompt;
    String pLower = prompt;
    pLower.toLowerCase();
    pLower.trim();

    // 1. Recall commands
    if (pLower == "what do you remember" || pLower == "what do you remember?" ||
        pLower == "show memory" || pLower == "recall" || pLower == "list memories" ||
        pLower == "what is in your memory" || pLower == "show my facts") {
        reply = recallAllKnowledge();
        return true;
    }

    // 2. Clear memory command
    if (pLower == "clear memory" || pLower == "reset memory" || pLower == "forget all") {
        clearAllKnowledge();
        reply = "GENESIS AI 5.0 memory bank has been completely cleared and reset.";
        return true;
    }

    // 3. Learning / Feeding patterns
    String factToSave = "";
    if (pLower.startsWith("remember that ")) {
        factToSave = p.substring(14);
    } else if (pLower.startsWith("remember ")) {
        factToSave = p.substring(9);
    } else if (pLower.startsWith("feed: ")) {
        factToSave = p.substring(6);
    } else if (pLower.startsWith("feed ")) {
        factToSave = p.substring(5);
    } else if (pLower.startsWith("store this: ")) {
        factToSave = p.substring(12);
    } else if (pLower.startsWith("learn that ")) {
        factToSave = p.substring(11);
    } else if (pLower.startsWith("note that ")) {
        factToSave = p.substring(10);
    } else if (pLower.startsWith("my name is ")) {
        factToSave = "User's name is " + p.substring(11);
    }

    factToSave.trim();
    if (factToSave.length() > 1) {
        feedKnowledge(factToSave);
        int c = getMemoryCount();
        reply = "Permanently memorized in GENESIS AI 5.0 on-chip flash: '" + factToSave + "'. Total facts in memory: " + String(c) + ".";
        return true;
    }

    return false;
}

#endif // GENESIS_MEMORY_ENGINE_H
