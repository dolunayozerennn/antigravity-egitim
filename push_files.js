const fs = require('fs');

const files = [
    "Projeler/WhatsApp_Onboarding/config/env.js",
    "Projeler/WhatsApp_Onboarding/server.js",
    "Projeler/WhatsApp_Onboarding/services/manychat.js",
    "Projeler/WhatsApp_Onboarding/services/phoneValidator.js",
    "Projeler/WhatsApp_Onboarding/package.json",
    "_knowledge/bekleyen-gorevler.md",
    "_knowledge/calisma-kurallari.md"
];

const out = [];
for (const f of files) {
    try {
        const content = fs.readFileSync(f, 'utf8');
        out.push({
            path: f,
            content: content
        });
    } catch (e) {
        console.error(`Error reading ${f}: ${e.message}`);
    }
}

fs.writeFileSync("push_files.json", JSON.stringify(out));
