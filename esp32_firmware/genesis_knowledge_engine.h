#ifndef GENESIS_KNOWLEDGE_ENGINE_H
#define GENESIS_KNOWLEDGE_ENGINE_H

#include <Arduino.h>
#include <math.h>

struct KnowledgeEntry {
    const char* keywords; // comma-separated lowercase keywords
    const char* answer;
};

static const KnowledgeEntry ON_CHIP_ENCYCLOPEDIA[] PROGMEM = {
    // --- CONVERSATIONAL, CAPABILITIES & IDENTITY ---
    {"what can you do,what you can do,your capabilities,help me,features,what do you do,how do you work",
     "I can answer any world knowledge, science, coding, history, or math question, track live ISS satellite telemetry (NORAD-25544) & NOAA space weather, and remember facts for you!"},
    {"who are you,what are you,your name,created you,made you,built you,ishit jain,creator",
     "I am GENESIS GPT-4o OMNI, a sovereign AI terminal created and architected by Ishit Jain on your 240MHz RISC-V ESP32-C5 with a 320x240 landscape display."},
    {"how are you,how r u,how is it going,are you ok,whats up,what's up",
     "All cognitive, satellite telemetry, and world-knowledge systems are 100% online at 240MHz! Ask me any question about science, space, math, coding, or the world."},
    {"thank you,thanks,good job,awesome,great,nice,cool,love you",
     "You are very welcome, Ishit Jain! I am always ready to help. Ask me another question anytime!"},

    // --- SATELLITES, SPACECRAFT & ORBITAL TELEMETRY ---
    {"satellite,iss,international space station,norad,25544,orbit",
     "ISS (NORAD-25544) orbits Earth in Low Earth Orbit at ~420 km altitude, traveling at 27,580 km/h (7.66 km/s) and completing 15.5 orbits every day."},
    {"gps,navic,glonass,galileo,navigation satellite",
     "Global navigation satellites (GPS, India's NavIC, Galileo, GLONASS) orbit in Medium Earth Orbit (~20,200 km) with atomic clocks to triangulate position within meters."},
    {"starlink,leo constellation,space internet",
     "SpaceX Starlink is a Low Earth Orbit megaconstellation at ~550 km altitude using optical laser inter-satellite links to deliver high-speed internet worldwide."},
    {"james webb,jwst,infrared telescope,lagrange",
     "The James Webb Space Telescope (JWST) orbits the Sun-Earth L2 Lagrange point 1.5 million km from Earth, using a 6.5m gold-coated mirror to observe early galaxies in infrared."},
    {"hubble,space telescope,hst",
     "Deployed in 1990 at 540 km altitude, the Hubble Space Telescope revolutionized astronomy by measuring the universe's expansion rate and imaging deep-space nebulae."},
    {"voyager,interstellar,golden record,deep space",
     "Launched in 1977, Voyager 1 and Voyager 2 are the farthest human-made spacecraft, actively transmitting telemetry from interstellar space over 24 billion km away."},
    {"chandrayaan,isro,pragyan,vikram,aditya l1,mangalyaan",
     "ISRO's Chandrayaan-3 made history on August 23, 2023 as the first mission to soft-land near the Moon's south pole, followed by India's Aditya-L1 solar observatory."},
    {"noaa,space weather,solar storm,kp index,aurora,geomagnetic",
     "NOAA Space Weather satellites monitor solar flares, coronal mass ejections, and the planetary Kp-index (0-9) to forecast geomagnetic storms and auroras."},
    {"kepler,orbital mechanics,escape velocity,geostationary",
     "Earth's escape velocity is 11.186 km/s. Geostationary satellites orbit above the equator at 35,786 km altitude, matching Earth's 24-hour rotation period."},

    // --- SOLAR SYSTEM & ASTRONOMY ---
    {"mercury,closest planet",
     "Mercury is the smallest and innermost planet in the Solar System, orbiting the Sun every 88 Earth days with surface temperatures swinging from -180 C to 430 C."},
    {"venus,hottest planet,morning star",
     "Venus is the second planet from the Sun and the hottest planet (465 C) due to a dense carbon dioxide atmosphere creating a runaway greenhouse effect."},
    {"earth,our planet,third planet,age of earth,circumference",
     "Earth is the third planet from the Sun, formed 4.54 billion years ago, with a 12,742 km diameter, 71% ocean coverage, and a protective nitrogen-oxygen atmosphere."},
    {"mars,red planet,olympus mons,perseverance",
     "Mars is the fourth planet from the Sun (228 million km out), colored red by iron oxide dust, home to Olympus Mons (the tallest volcano in the Solar System)."},
    {"jupiter,largest planet,great red spot,fifth planet",
     "Jupiter is the fifth planet from the Sun (~778 million km out) and the largest planet in our Solar System (318 Earth masses) with 95 known moons including Ganymede."},
    {"saturn,ringed planet,titan,enceladus,sixth planet",
     "Saturn is the sixth planet from the Sun (~1.4 billion km out), famous for its spectacular icy ring system and 146 moons including Titan and Enceladus."},
    {"uranus,neptune,ice giants,pluto,dwarf planet",
     "Uranus (7th planet, tilted 98 degrees on its side) and Neptune (8th planet, 4.5 billion km from the Sun with supersonic winds) are the Solar System's ice giants."},
    {"sun,solar system,eight planets,milky way",
     "Our Solar System has 8 planets orbiting the Sun, a G-type star 149.6 million km from Earth powered by nuclear fusion converting 600M tons of hydrogen/sec into helium."},
    {"moon,lunar,tides,apollo 11,neil armstrong",
     "Earth's Moon orbits at 384,400 km, stabilizes Earth's axial tilt, drives ocean tides, and was first walked on by Neil Armstrong and Buzz Aldrin on July 20, 1969."},
    {"universe,big bang,13.8 billion,galaxies,andromeda",
     "The observable universe began 13.8 billion years ago in the Big Bang, spans 93 billion light-years across, and holds over 2 trillion galaxies."},
    {"black hole,hawking,event horizon,singularity",
     "Black holes are regions of extreme spacetime curvature where escape velocity exceeds light speed. Quantum effects near the event horizon emit Hawking radiation."},

    // --- INVENTIONS, SCIENTISTS & PIONEERS ---
    {"telephone,alexander graham bell,invented phone",
     "Alexander Graham Bell patented the first practical electric telephone in 1876, transforming global voice communication."},
    {"radio,marconi,wireless telegraph,j.c. bose",
     "Guglielmo Marconi and Sir Jagadish Chandra Bose pioneered wireless radio wave transmission in the 1890s, building on Maxwell and Hertz's electromagnetic laws."},
    {"light bulb,edison,incandescent,bulb",
     "Thomas Edison patented the commercially practical incandescent light bulb in 1879 using a carbonized bamboo filament lasting over 1,200 hours."},
    {"tesla,nikola,alternating current",
     "Nikola Tesla pioneered alternating current (AC) power grids, polyphase induction motors, wireless energy transfer, and high-voltage Tesla coils."},
    {"computer,turing,babbage,analytical engine,ada lovelace",
     "Charles Babbage designed the Analytical Engine, Ada Lovelace wrote the first algorithm, and Alan Turing formalized universal computation in 1936."},
    {"internet,world wide web,www,arpanet,tim berners",
     "The Internet evolved from ARPANET (1969) using TCP/IP by Vint Cerf and Bob Kahn, while Tim Berners-Lee invented the World Wide Web at CERN in 1989."},
    {"airplane,aeroplane,wright brothers,flight",
     "Orville and Wilbur Wright achieved the first powered, sustained, and controlled heavier-than-air airplane flight at Kitty Hawk on December 17, 1903."},
    {"steam engine,james watt,industrial revolution",
     "James Watt's 1776 separate-condenser steam engine dramatically boosted fuel efficiency, powering factories, locomotives, and the Industrial Revolution."},
    {"printing press,gutenberg,movable type",
     "Johannes Gutenberg introduced mechanical movable-type printing to Europe around 1440, sparking the Renaissance and the global spread of literacy."},
    {"marie curie,radium,polonium,radioactivity",
     "Marie Curie discovered polonium and radium, coined the term radioactivity, and remains the only person to win Nobel Prizes in both Physics and Chemistry."},
    {"raman,c.v. raman,raman effect,light scattering",
     "Sir C.V. Raman discovered the Raman Effect in 1928, showing that light changes wavelength when deflected by molecules, winning the 1930 Physics Nobel Prize."},
    {"apj abdul kalam,missile man,wings of fire",
     "Dr. A.P.J. Abdul Kalam was an aerospace scientist known as the Missile Man of India who played a pivotal role in ISRO and served as India's 11th President (2002-2007)."},

    // --- PHYSICS & QUANTUM MECHANICS ---
    {"quantum,qubit,superposition,entanglement,schrodinger",
     "Quantum computing uses qubits in superposition and quantum entanglement to evaluate vast multidimensional state spaces exponentially faster than classical computers."},
    {"relativity,einstein,spacetime,e=mc",
     "Einstein's General Relativity shows that gravity is the geometric curvature of four-dimensional spacetime caused by mass and energy, governed by E=mc^2."},
    {"gravity,newton,universal gravitation,apple,laws of motion",
     "Gravity attracts all mass and energy via F=G(m1*m2)/r^2. Newton's 3 Laws of Motion are Inertia, F=m*a, and Equal-and-Opposite Action-Reaction."},
    {"speed of light,299792458,fastest",
     "Light travels in a vacuum at exactly 299,792,458 meters per second (about 300,000 km/s), the absolute speed limit of causality and matter in the universe."},
    {"speed of sound,mach,sonic boom",
     "The speed of sound in dry air at 20 C is 343 meters per second (1,235 km/h, or Mach 1). Traveling faster than Mach 1 produces a supersonic shockwave (sonic boom)."},
    {"sky blue,rayleigh,atmosphere color,rainbow",
     "The sky is blue due to Rayleigh scattering: Earth's atmosphere scatters shorter, high-frequency blue wavelengths of sunlight much more strongly than red light."},
    {"thermodynamics,entropy,energy conservation",
     "The Laws of Thermodynamics state that energy cannot be created or destroyed (1st Law), and total entropy of an isolated system always increases over time (2nd Law)."},
    {"fusion,tokamak,iter,nuclear energy,fission",
     "Nuclear fission splits heavy nuclei like Uranium-235, while nuclear fusion merges light hydrogen isotopes into helium, releasing clean stellar-scale energy."},

    // --- CHEMISTRY, BIOLOGY & MEDICINE ---
    {"photosynthesis,chlorophyll,plants make food",
     "Photosynthesis converts sunlight, water (H2O), and carbon dioxide (CO2) into glucose (C6H12O6) and oxygen (O2) inside plant chloroplasts via chlorophyll."},
    {"dna,rna,genetics,double helix,chromosome,crispr",
     "DNA stores hereditary instructions in a double helix of four nucleotide bases (A, T, C, G). Cells transcribe DNA into RNA to synthesize functional proteins."},
    {"mitochondria,cell,powerhouse,atp",
     "Cells are the fundamental units of life. Mitochondria generate cellular energy by synthesizing adenosine triphosphate (ATP) through oxidative phosphorylation."},
    {"brain,neuron,synapse,nervous system",
     "The human brain contains 86 billion neurons linked by over 100 trillion synapses, processing thought, memory, and consciousness via electrochemical signals."},
    {"heart,blood,circulation,arteries,human body,bones",
     "The human body has 206 bones in adults, while the heart beats ~100,000 times daily to pump 5 liters of oxygen-rich blood across 100,000 km of blood vessels."},
    {"atom,proton,neutron,electron,nucleus,quark",
     "Atoms consist of a dense nucleus of positively charged protons and neutral neutrons (made of quarks), surrounded by quantum orbitals of negatively charged electrons."},
    {"periodic table,mendeleev,elements,atomic number",
     "Dmitri Mendeleev formulated the Periodic Table, organizing all 118 known chemical elements by atomic number (proton count) and electron shell configuration."},
    {"water,h2o,boiling point,freezing point",
     "Water (H2O) consists of two hydrogen atoms bonded to one oxygen atom at a 104.5-degree angle, freezing at 0 C and boiling at 100 C at standard pressure."},
    {"table salt,nacl,sodium chloride,gold,au,iron,fe,diamond,carbon",
     "Table salt is sodium chloride (NaCl). Common element symbols include Gold (Au, #79), Silver (Ag, #47), Iron (Fe, #26), Carbon (C, #6), and Oxygen (O, #8)."},
    {"evolution,darwin,natural selection",
     "Charles Darwin's theory of evolution by natural selection explains how species adapt and diversify over generations through heritable traits that improve survival."},
    {"vaccine,immune system,antibody,pasteur,jenner",
     "Vaccines train the adaptive immune system to produce targeted antibodies and memory T-cells against pathogens without causing the disease itself."},
    {"antibiotic,penicillin,fleming,bacteria,virus",
     "Alexander Fleming discovered penicillin in 1928, the first antibiotic capable of curing bacterial infections by disrupting bacterial cell wall synthesis."},

    // --- ELECTRONICS, AI & COMPUTER SCIENCE ---
    {"electricity,voltage,current,ohm,circuit",
     "Electricity is the flow of electric charge (electrons). Ohm's Law (V = I * R) relates Voltage (V, Volts), Current (I, Amperes), and Resistance (R, Ohms)."},
    {"transistor,semiconductor,silicon,microchip",
     "Invented at Bell Labs in 1947, the semiconductor transistor acts as a nanoscale electronic switch and amplifier, forming the building block of all modern CPUs."},
    {"ai,how does ai,what is ai,neural network,transformer,gpt,deep learning,llm,machine learning,artificial intelligence",
     "AI works by training deep neural networks and Transformer attention models on massive datasets to recognize patterns, reason, and generate text, code, and decisions."},
    {"python,programming,coding,algorithm,software,java,javascript",
     "Python leads AI and data science, JavaScript powers interactive web apps, and C/C++ delivers bare-metal real-time speed on microcontrollers like ESP32-C5."},
    {"c++,arduino,firmware,embedded,spi,i2c,uart",
     "C++ compiles to native RISC-V machine code, controlling hardware buses like SPI (high-speed display), I2C (sensors), and UART (serial communication)."},
    {"risc-v,esp32-c5,microcontroller,wifi 6",
     "Your ESP32-C5 features a 240MHz 32-bit RISC-V processor, 384KB SRAM, and industry-first dual-band (2.4GHz + 5GHz) Wi-Fi 6 (802.11ax) + Bluetooth 5 LE."},
    {"bitcoin,blockchain,cryptography,satoshi,crypto",
     "Introduced in 2008 by Satoshi Nakamoto, Bitcoin is a decentralized peer-to-peer digital currency secured by SHA-256 proof-of-work cryptography on a public blockchain."},

    // --- WORLD GEOGRAPHY, COUNTRIES, LEADERS & HISTORY ---
    {"india,new delhi,bharat,narendra modi,prime minister of india,president of india,droupadi murmu",
     "India is the world's largest democracy (capital: New Delhi). Narendra Modi is the Prime Minister of India, and Droupadi Murmu is the President of India."},
    {"usa,united states,washington,president of usa,america",
     "The United States has 50 states with Washington, D.C. as its capital and New York City as its largest metropolitan and financial center."},
    {"japan,tokyo,mount fuji",
     "The capital of Japan is Tokyo, the world's most populous metropolitan area and a global leader in robotics, semiconductors, and high-speed Shinkansen rail."},
    {"france,paris,uk,london,germany,berlin,italy,rome,spain,madrid",
     "Major European capitals: France is Paris, the United Kingdom is London, Germany is Berlin, Italy is Rome, and Spain is Madrid."},
    {"china,beijing,russia,moscow,australia,canberra,canada,ottawa,brazil,brasilia,kazakhstan,astana",
     "World capitals: China is Beijing, Russia is Moscow, Kazakhstan is Astana, Australia is Canberra, Canada is Ottawa, and Brazil is Brasilia."},
    {"continents,seven continents,countries in the world,largest country,smallest country",
     "Earth has 7 continents and 195 sovereign countries. Russia is the largest country by area, Vatican City is the smallest, and India & China are the most populous."},
    {"mount everest,highest mountain,himalaya,k2",
     "Mount Everest in the Himalayas is Earth's highest mountain above sea level at 8,848.86 meters (29,031.7 feet), followed by K2 at 8,611 meters."},
    {"ocean,pacific,mariana trench,earth surface,nile,amazon river,sahara",
     "Oceans cover 71% of Earth (Pacific is deepest at 10,935m in the Mariana Trench). The Nile (6,650 km) and Amazon (6,400 km) are Earth's longest rivers."},
    {"elon musk,spacex,neuralink",
     "Elon Musk is the CEO of SpaceX and Tesla, leading reusable orbital rocketry (Starship), global satellite internet (Starlink), electric vehicles, and xAI."},
    {"sam altman,openai,chatgpt,sundar pichai,satya nadella,tim cook,jensen huang",
     "Tech leaders: Sam Altman leads OpenAI, Sundar Pichai leads Google/Alphabet, Satya Nadella leads Microsoft, Jensen Huang leads NVIDIA, and Tim Cook leads Apple."},
    {"world war,ww1,ww2,history,united nations,mahatma gandhi,independence",
     "World War I lasted 1914-1918 and World War II lasted 1939-1945. India gained independence on August 15, 1947 after a historic movement led by Mahatma Gandhi and freedom fighters."},
    {"ancient egypt,pyramids,giza,mesopotamia,indus valley",
     "Early human civilizations arose in Mesopotamia, the Indus Valley (Harappa/Mohenjo-daro), and Ancient Egypt, which built the Great Pyramid of Giza around 2560 BCE."},
    {"philosophy,socrates,plato,aristotle,stoicism",
     "Classical philosophy examines existence, knowledge, and ethics: Socrates pioneered dialectical inquiry, Plato founded the Academy, and Aristotle formalized logic."},
    {"pi,circle,pythagoras,geometry,calculus,fibonacci",
     "Pi (3.14159265...) is a circle's circumference-to-diameter ratio. Calculus (Newton & Leibniz) models continuous change via derivatives and integrals."},
    {"joke,funny,laugh,humor",
     "Why do satellites never get lonely in orbit? Because they always have great reception and 15.5 sunrises every day!"}
};

static const int ON_CHIP_KB_COUNT = sizeof(ON_CHIP_ENCYCLOPEDIA) / sizeof(ON_CHIP_ENCYCLOPEDIA[0]);

inline String evaluateAdvancedMathAndUnits(const String& rawPrompt) {
    String s = rawPrompt;
    s.toLowerCase();
    s.trim();

    // Square root handling: "sqrt 144", "square root of 256"
    int sqIdx = s.indexOf("sqrt");
    if (sqIdx < 0) sqIdx = s.indexOf("square root");
    if (sqIdx >= 0) {
        String numPart = "";
        for (size_t i = sqIdx; i < s.length(); i++) {
            char c = s.charAt(i);
            if (isDigit(c) || c == '.') numPart += c;
            else if (numPart.length() > 0) break;
        }
        if (numPart.length() > 0) {
            double v = numPart.toDouble();
            double r = sqrt(v);
            if (floor(r) == r) return "Calculated Result: sqrt(" + numPart + ") = " + String((long)r);
            return "Calculated Result: sqrt(" + numPart + ") = " + String(r, 4);
        }
    }

    // Percentage handling: "15% of 200"
    int pctIdx = s.indexOf("% of");
    if (pctIdx > 0) {
        String left = s.substring(0, pctIdx);
        String right = s.substring(pctIdx + 4);
        left.trim();
        right.trim();
        double a = left.toDouble();
        double b = right.toDouble();
        if (a != 0 || left == "0") {
            double res = (a / 100.0) * b;
            return "Calculated Result: " + String(res, 2);
        }
    }

    // Clean arithmetic expression
    String expr = s;
    expr.replace("calculate", "");
    expr.replace("what is", "");
    expr.replace("whats", "");
    expr.replace("solve", "");
    expr.replace("evaluate", "");
    expr.replace("plus", "+");
    expr.replace("minus", "-");
    expr.replace("times", "*");
    expr.replace("multiplied by", "*");
    expr.replace("divided by", "/");
    expr.replace("?", "");
    expr.replace("=", "");
    expr.replace(" ", "");
    expr.trim();

    char op = 0;
    int opIdx = -1;
    for (int i = 1; i < (int)expr.length(); i++) {
        char c = expr.charAt(i);
        if (c == '+' || c == '-' || c == '*' || c == '/' || c == '^' || c == '%') {
            op = c;
            opIdx = i;
            break;
        }
    }

    if (opIdx > 0 && opIdx < (int)expr.length() - 1) {
        String leftStr = expr.substring(0, opIdx);
        String rightStr = expr.substring(opIdx + 1);
        bool leftValid = isDigit(leftStr.charAt(0)) || leftStr.charAt(0) == '-';
        bool rightValid = isDigit(rightStr.charAt(0)) || rightStr.charAt(0) == '-';
        for (size_t i = 1; i < leftStr.length(); i++) {
            if (!isDigit(leftStr.charAt(i)) && leftStr.charAt(i) != '.') leftValid = false;
        }
        for (size_t i = 1; i < rightStr.length(); i++) {
            if (!isDigit(rightStr.charAt(i)) && rightStr.charAt(i) != '.') rightValid = false;
        }
        if (leftValid && rightValid) {
            double a = leftStr.toDouble();
            double b = rightStr.toDouble();
            double res = 0;
            if (op == '+') res = a + b;
            else if (op == '-') res = a - b;
            else if (op == '*') res = a * b;
            else if (op == '/') {
                if (b == 0) return "Math Error: Division by zero is undefined.";
                res = a / b;
            }
            else if (op == '^') res = pow(a, b);
            else if (op == '%') res = (long)a % (long)b;

            if (floor(res) == res) return "Calculated Result: " + leftStr + " " + String(op) + " " + rightStr + " = " + String((long)res);
            return "Calculated Result: " + leftStr + " " + String(op) + " " + rightStr + " = " + String(res, 4);
        }
    }
    return "";
}

inline String queryOnChipKnowledgeBase(const String& rawPrompt) {
    String q = rawPrompt;
    q.toLowerCase();
    q.replace("?", "");
    q.replace("!", "");
    q.replace(".", "");
    q.trim();

    int bestScore = 0;
    int bestIdx = -1;

    for (int i = 0; i < ON_CHIP_KB_COUNT; i++) {
        String kwList = String(ON_CHIP_ENCYCLOPEDIA[i].keywords);
        int score = 0;
        int start = 0;
        while (start < (int)kwList.length()) {
            int comma = kwList.indexOf(',', start);
            if (comma < 0) comma = kwList.length();
            String kw = kwList.substring(start, comma);
            kw.trim();
            if (kw.length() > 0 && q.indexOf(kw) >= 0) {
                score += kw.length() * 3;
            }
            start = comma + 1;
        }
        if (score > bestScore) {
            bestScore = score;
            bestIdx = i;
        }
    }

    if (bestIdx >= 0 && bestScore > 0) {
        return String(ON_CHIP_ENCYCLOPEDIA[bestIdx].answer);
    }
    return "";
}

#endif // GENESIS_KNOWLEDGE_ENGINE_H
