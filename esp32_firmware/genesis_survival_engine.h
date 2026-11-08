#ifndef GENESIS_SURVIVAL_ENGINE_H
#define GENESIS_SURVIVAL_ENGINE_H

#include <Arduino.h>

// ==============================================================================
// GENESIS AI 5.0 - DISASTER SURVIVAL & EMERGENCY MEDICAL ENGINE (OFFLINE)
// ==============================================================================
// 100% On-Chip Autonomous Survival Knowledge for Grid Failures, Wars, Natural
// Disasters, Medical Emergencies, and Off-Grid Wilderness Survival.
// Stored in internal flash — requires ZERO internet and ZERO external storage.
// ==============================================================================

struct SurvivalTopic {
    const char* trigger;
    const char* title;
    const char* guidance;
};

// Encyclopedic offline disaster & emergency survival database
const SurvivalTopic SURVIVAL_DB[] PROGMEM = {
    // 1. LIFE-THREATENING MEDICAL EMERGENCIES
    {
        "cpr",
        "EMERGENCY CPR PROTOCOL",
        "1. Check responsiveness and breathing. Call for help.\n"
        "2. Place heel of hand on center of chest, other hand on top.\n"
        "3. Push hard & fast: 100-120 compressions/min, 2 inches (5cm) deep.\n"
        "4. Ratio: 30 chest compressions followed by 2 rescue breaths.\n"
        "5. Continue without stopping until victim breathes or medics arrive."
    },
    {
        "bleeding",
        "SEVERE ARTERIAL BLEEDING",
        "1. Apply direct firm pressure with sterile cloth or clean fabric.\n"
        "2. Do NOT remove soaked pads; add more layers on top.\n"
        "3. If limb bleeding does not stop: Apply TOURNIQUET 2-3 inches above wound (never on joint).\n"
        "4. Tighten windlass until bleeding halts completely. Lock rod in place.\n"
        "5. Mark exact application time (e.g., T: 14:30) on forehead."
    },
    {
        "tourniquet",
        "TOURNIQUET APPLICATION",
        "1. Place 2-3 inches (5-7cm) proximal to the wound (between wound and heart).\n"
        "2. Never place over an elbow or knee joint.\n"
        "3. Twist windlass rod until bright red spurting bleeding stops completely.\n"
        "4. Secure the rod firmly in the clip.\n"
        "5. Note exact time applied. Do NOT loosen until surgical care is reached."
    },
    {
        "choking",
        "CHOKING (HEIMLICH MANEUVER)",
        "1. If coughing, encourage continued coughing. Do not slap back.\n"
        "2. If silent/unable to breathe: Stand behind person, lean them forward.\n"
        "3. Give 5 sharp back blows between shoulder blades with heel of hand.\n"
        "4. Make fist above navel, grasp with other hand, deliver 5 quick upward abdominal thrusts.\n"
        "5. Repeat until object is expelled. If unconscious, begin CPR."
    },
    {
        "burn",
        "BURN TREATMENT PROTOCOL",
        "1. Stop burning source immediately.\n"
        "2. Cool burn under clean running cool water for 15-20 minutes. NEVER use ice or ice water.\n"
        "3. Do NOT pop blisters or apply butter, grease, or ointments.\n"
        "4. Cover loosely with clean, dry, non-stick sterile gauze or plastic wrap.\n"
        "5. Keep patient warm to prevent shock. Elevate burned limbs above heart level."
    },
    {
        "fracture",
        "BONE FRACTURE & SPRAIN (R.I.C.E)",
        "1. Immobilize bone above and below the suspected fracture site.\n"
        "2. Splint using rigid material (wood, branch, rolled magazine) padded with cloth.\n"
        "3. Tie splint securely with strips of cloth; do NOT wrap so tight it cuts blood circulation.\n"
        "4. R.I.C.E: Rest injured limb, Ice/cold pack wrapped in cloth, Compress, Elevate.\n"
        "5. Check fingers/toes for pulse, warmth, and sensation every 15 minutes."
    },
    {
        "snakebite",
        "SNAKEBITE EMERGENCY",
        "1. Move out of striking range. Keep calm and stay still.\n"
        "2. Keep bitten limb IMMOBILIZED below heart level.\n"
        "3. Remove rings, watches, and tight clothing before swelling starts.\n"
        "4. DO NOT cut wound, DO NOT suck venom, DO NOT apply ice or a tourniquet.\n"
        "5. Wrap limb with wide elastic bandage from fingers/toes upwards with moderate pressure."
    },
    {
        "hypothermia",
        "HYPOTHERMIA PROTOCOL",
        "1. Move to warm, sheltered area out of wind and rain.\n"
        "2. Gently remove wet clothing; replace with dry layers, blankets, or sleeping bag.\n"
        "3. Insulate body from frozen ground with pine boughs, cardboard, or foam.\n"
        "4. Warm core first (chest, neck, groin) with warm water bottles or skin-to-skin contact.\n"
        "5. Give warm sweet drinks if conscious. NEVER give alcohol. Do not rub frostbitten skin."
    },
    {
        "heatstroke",
        "HEATSTROKE / HYPERTHERMIA",
        "1. Symptoms: Hot, red, dry/sweaty skin, confusion, rapid pulse, body temp >40C (104F).\n"
        "2. Move to shade or cool area immediately. Remove outer excess clothing.\n"
        "3. Rapid active cooling: Soak with cool water, fan aggressively, place ice packs in armpits, groin, neck.\n"
        "4. Elevate feet slightly. If conscious, give cool water with a pinch of salt."
    },

    // 2. WATER PURIFICATION & EDIBLE SURVIVAL
    {
        "water",
        "OFFLINE WATER PURIFICATION",
        "1. BOILING: Bring water to rolling boil for 1 full minute (3 min if altitude >2000m). Kills all pathogens.\n"
        "2. CHEMICAL: Add 2 drops of unscented household bleach (5-6% sodium hypochlorite) per 1 liter of clear water. Stir and wait 30 minutes.\n"
        "3. SODIS (Solar): Fill clear PET plastic bottle, expose to direct intense sunlight for 6 hours.\n"
        "4. DIY FILTER: Layer crushed charcoal, sand, fine gravel, and cloth in plastic bottle with hole in base."
    },
    {
        "filter",
        "BIO-SAND CHARCOAL FILTER",
        "1. In an inverted plastic bottle, puncture small holes in bottom cap.\n"
        "2. Bottom layer: Clean cloth or cotton fabric.\n"
        "3. Middle layer: 3 inches of crushed hardwood campfire charcoal (absorbs chemical toxins).\n"
        "4. Upper layer: 3 inches of fine washed sand followed by 2 inches of coarse gravel.\n"
        "5. Pour murky water through; always boil the filtered water before drinking."
    },

    // 3. FIRE & SHELTER
    {
        "fire",
        "OFFLINE FIRE MAKING METHODS",
        "1. Tinder: Dry birch bark, pine resin, dry grass, frayed cotton cloth, crushed dry leaves.\n"
        "2. Battery + Wire/Foil: Touch wire or chewing gum aluminum foil wrapper across battery terminals.\n"
        "3. Magnifying Lens: Focus direct sunbeam into pinpoint focal dot on dark char cloth or dry fungus.\n"
        "4. Bow Drill: Carve hardwood spindle and softwood hearth board with V-shaped notch.\n"
        "5. Always protect embers from wind; gently blow while adding dry kindling."
    },
    {
        "shelter",
        "EMERGENCY DEBRIS SHELTER",
        "1. Location: High ground away from flash flood valleys, dead falling trees, or rockslides.\n"
        "2. Frame: Place 8-10 foot ridgepole branch angled at 45 degrees against sturdy tree trunk.\n"
        "3. Ribs: Lean sturdy rib branches along both sides of ridgepole to create an A-frame.\n"
        "4. Bedding: Fill inside with 2-3 feet of dry leaves/pine needles to insulate body from cold earth.\n"
        "5. Thatch: Cover exterior with 2-3 feet of leafy branches and earth to shed rain and retain heat."
    },

    // 4. DISASTER PROTOCOLS (NATURAL & MAN-MADE)
    {
        "nuclear",
        "NUCLEAR FALLOUT & RADIATION",
        "1. Get inside: Concrete, brick, or underground basement (10x more protection than wood).\n"
        "2. Seal: Turn off ventilation, close windows, doors, and fireplace dampers.\n"
        "3. Decontaminate: Remove outer clothing before entering shelter; wash hair & skin gently with soap.\n"
        "4. Radioactive decay: Fallout radiation drops by 90% after 7 hours and 99% after 48 hours.\n"
        "5. Stay shielded inside for minimum 24-72 hours until official broadcast clears safe evacuation."
    },
    {
        "radiation",
        "NUCLEAR FALLOUT & RADIATION",
        "1. Get inside: Concrete, brick, or underground basement (10x more protection than wood).\n"
        "2. Seal: Turn off ventilation, close windows, doors, and fireplace dampers.\n"
        "3. Decontaminate: Remove outer clothing before entering shelter; wash hair & skin gently with soap.\n"
        "4. Radioactive decay: Fallout radiation drops by 90% after 7 hours and 99% after 48 hours.\n"
        "5. Stay shielded inside for minimum 24-72 hours until official broadcast clears safe evacuation."
    },
    {
        "earthquake",
        "EARTHQUAKE SURVIVAL PROTOCOL",
        "1. INDOORS: DROP, COVER, and HOLD ON under sturdy table, desk, or against interior wall.\n"
        "2. Stay away from windows, glass, heavy mirrors, bookcases, and hanging light fixtures.\n"
        "3. Do NOT run outside during shaking. Do NOT use elevators.\n"
        "4. OUTDOORS: Move to open area away from power lines, buildings, overpasses, and brick chimneys.\n"
        "5. AFTERSHOCKS: Expect secondary earthquakes; check gas and water lines for leaks."
    },
    {
        "flood",
        "FLASH FLOOD PROTOCOL",
        "1. Move immediately to higher ground. Do not wait for instructions.\n"
        "2. Turn Around, Don't Drown: 6 inches of rapid water knocks an adult down; 12 inches floats cars.\n"
        "3. Never walk or swim through floodwater (debris, downed power lines, raw sewage).\n"
        "4. If trapped in building: Go to highest level. Do not climb into closed attic without roof exit.\n"
        "5. If car stalls in rising water: Abandon immediately and move to high ground."
    },
    {
        "tsunami",
        "TSUNAMI EVACUATION",
        "1. Warning signs: Severe coastal earthquake or sudden abnormal recession of ocean shoreline.\n"
        "2. Move inland immediately to elevation at least 100 feet (30m) above sea level or 2 miles inland.\n"
        "3. Do NOT wait for official siren or go to beach to watch the receding tide.\n"
        "4. Tsunamis arrive in multiple waves over several hours; second/third wave is often largest.\n"
        "5. Stay on high ground until emergency authorities confirm the all-clear."
    },
    {
        "tornado",
        "TORNADO SHELTER PROTOCOL",
        "1. Go to lowest level: Storm cellar, basement, or safe room.\n"
        "2. If no basement: Interior hallway or bathroom on lowest floor, away from windows.\n"
        "3. Protect head and neck with arms, thick blankets, pillows, or bicycle helmet.\n"
        "4. In vehicle or mobile home: Abandon immediately and seek sturdy permanent building or low ditch."
    },
    {
        "hurricane",
        "HURRICANE / CYCLONE SURVIVAL",
        "1. Secure home: Board windows with 5/8-inch marine plywood. Anchor outdoor furniture.\n"
        "2. Store water: Fill bathtubs, clean containers (1 gallon per person per day for 7 days).\n"
        "3. Eye of the storm: Beware temporary calm; winds will resume violently from opposite direction.\n"
        "4. Stay indoors on lowest floor away from windows until entire storm passes."
    },

    // 5. RESCUE SIGNALING & MORSE CODE
    {
        "morse",
        "INTERNATIONAL MORSE CODE & SOS",
        "SOS = ... --- ... (3 short, 3 long, 3 short)\n"
        "A: .-   B: -... C: -.-. D: -..\n"
        "E: .    F: ..-. G: --.  H: ....\n"
        "I: ..   J: .--- K: -.-  L: .-..\n"
        "M: --   N: -.   O: ---  P: .--.\n"
        "Q: --.- R: .-.  S: ...  T: -\n"
        "U: ..-  V: ...- W: .--  X: -..-\n"
        "Y: -.-- Z: --..\n"
        "Emergency: 3 audio blasts, 3 smoke puffs, or 3 flashes of light."
    },
    {
        "sos",
        "EMERGENCY SOS SIGNALING",
        "1. Optical: Flash light 3 SHORT (0.5s), 3 LONG (1.5s), 3 SHORT (0.5s) = ... --- ...\n"
        "2. Acoustic: Blow whistle 3 times, pause 1 minute, repeat 3 times.\n"
        "3. Ground-to-Air: Lay out 3 parallel lines of branches, clothing, or rocks, or giant 'V' (Require Assistance) or 'X' (Medical Assistance).\n"
        "4. Mirror: Hold two fingers in V-shape targeting plane/boat, reflect sun flash across fingers."
    },
    {
        "signal",
        "GROUND-TO-AIR RESCUE SIGNALS",
        "Standard Ground Markers (min 10ft / 3m long with high contrast rocks/branches):\n"
        "V = Require Assistance\n"
        "X = Require Medical Assistance\n"
        "N = No / Negative\n"
        "Y = Yes / Affirmative\n"
        "-> = Proceeding in this direction\n"
        "Smoke: White smoke (green foliage) against dark ground; Black smoke (rubber/oil) on snow."
    },

    // 6. NAVIGATION WITHOUT COMPASS/GPS
    {
        "navigation",
        "OFFLINE CELESTIAL ORIENTEERING",
        "1. NORTH STAR (Northern Hemisphere): Find Big Dipper bowl outer 2 pointer stars. Follow line 5 times distance to locate Polaris (True North).\n"
        "2. SOUTHERN CROSS (Southern Hemisphere): Extend long axis of Crux cross 4.5 times down to find South.\n"
        "3. SUN & STICK: Place stick in ground, mark tip shadow. Wait 20 min, mark new tip shadow. Line connecting 1st to 2nd marker runs West to East.\n"
        "4. ANALOG WATCH: Point hour hand at sun. Halfway angle between hour hand and 12 o'clock points South (North in Southern hemisphere)."
    },
    {
        "compass",
        "OFFLINE CELESTIAL ORIENTEERING",
        "1. NORTH STAR: Find Big Dipper pointer stars. Line leads to Polaris (True North).\n"
        "2. SOUTHERN CROSS: Extend long axis 4.5x downward toward horizon for South.\n"
        "3. SHADOW STICK: Stick in ground; 1st shadow tip to 2nd shadow tip (20m later) points West-to-East.\n"
        "4. WATCH METHOD: Point hour hand at sun; bisect angle between hour hand and 12 for South."
    }
};

const int SURVIVAL_TOPICS_COUNT = sizeof(SURVIVAL_DB) / sizeof(SURVIVAL_DB[0]);

// Function to check if prompt is survival-related and return response
bool checkAndProcessSurvival(const String& prompt, String& titleOut, String& guidanceOut) {
    String pLower = prompt;
    pLower.toLowerCase();
    pLower.trim();

    // Check specific triggers
    for (int i = 0; i < SURVIVAL_TOPICS_COUNT; i++) {
        String trig = FPSTR(SURVIVAL_DB[i].trigger);
        if (pLower.indexOf(trig) >= 0) {
            titleOut = FPSTR(SURVIVAL_DB[i].title);
            guidanceOut = FPSTR(SURVIVAL_DB[i].guidance);
            return true;
        }
    }

    // Generic survival trigger
    if (pLower.indexOf("survival") >= 0 || pLower.indexOf("disaster") >= 0 || pLower.indexOf("emergency") >= 0 || pLower.indexOf("first aid") >= 0) {
        titleOut = "GENESIS AI 5.0 EMERGENCY SURVIVAL PROTOCOLS";
        guidanceOut = "Offline Disaster Survival Engine active. Available modules:\n"
                      "1. CPR & Severe Bleeding (Tourniquet)\n"
                      "2. Water Purification (Boiling, Bleach, Charcoal)\n"
                      "3. Fire & Debris Shelter Building\n"
                      "4. Nuclear Fallout, Earthquake, Flood & Tsunami\n"
                      "5. Morse Code & SOS Signaling\n"
                      "6. Celestial Navigation (North Star, Sun & Stick)\n"
                      "Ask any specific emergency topic (e.g., 'CPR', 'Bleeding', 'Water', 'Nuclear').";
        return true;
    }

    return false;
}

#endif // GENESIS_SURVIVAL_ENGINE_H
