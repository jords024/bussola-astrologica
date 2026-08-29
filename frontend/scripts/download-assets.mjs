import fs from "node:fs";
import path from "node:path";

const LOVABLE_BASE = "https://b26bc652-be79-46f9-8e21-7a7ecf8492c5.lovableproject.com";
const ASSETS_DIR = path.resolve("src/assets");
const PUBLIC_DIR = path.resolve("public");

function findAssetJsonFiles(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      results = results.concat(findAssetJsonFiles(fullPath));
    } else if (file.endsWith(".asset.json")) {
      results.push(fullPath);
    }
  }
  return results;
}

async function downloadAll() {
  const files = findAssetJsonFiles(ASSETS_DIR);
  console.log(`Encontrados ${files.length} arquivos de asset para baixar...`);

  for (const file of files) {
    const content = JSON.parse(fs.readFileSync(file, "utf-8"));
    const urlPath = content.url;
    if (!urlPath) continue;

    const targetPath = path.join(PUBLIC_DIR, urlPath);
    const targetDir = path.dirname(targetPath);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const downloadUrl = `${LOVABLE_BASE}${urlPath}`;
    console.log(`Baixando: ${content.original_filename} de ${downloadUrl}...`);

    try {
      const res = await fetch(downloadUrl);
      if (!res.ok) {
        console.error(`Erro ao baixar ${downloadUrl}: ${res.status} ${res.statusText}`);
        continue;
      }
      const buffer = Buffer.from(await res.arrayBuffer());
      fs.writeFileSync(targetPath, buffer);
      console.log(`Salvo com sucesso em: ${targetPath} (${buffer.length} bytes)`);
    } catch (err) {
      console.error(`Falha ao baixar ${downloadUrl}:`, err);
    }
  }

  console.log("Todos os assets foram baixados com sucesso para public/");
}

downloadAll();
