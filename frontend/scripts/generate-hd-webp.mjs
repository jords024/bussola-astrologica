import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const PUBLIC_DIR = path.resolve(import.meta.dirname, "../public/__l5e/assets-v1");
const ASSETS_DIR = path.resolve(import.meta.dirname, "../src/assets");

const filesToConvert = [
  {
    src: "9925f88c-b725-4dda-88e0-4591cbbf9709/crassus-retrato.png",
    dest: "crassus-retrato.webp",
    width: 1400,
    quality: 94,
  },
  {
    src: "2345876f-1ae6-4926-907b-d74c909ea1f1/bussola-tudo-flui.png",
    dest: "bussola-tudo-flui.webp",
    width: 1400,
    quality: 92,
  },
  {
    src: "4f91cc26-ad57-440b-8810-e153452abbad/bussola-tudo-flui-mobile.png",
    dest: "bussola-tudo-flui-mobile.webp",
    width: 1080,
    quality: 92,
  },
  {
    src: "6beded8b-6c93-4d91-8c10-b9ba337a09fa/bussola-semana-seguinte.png",
    dest: "bussola-semana-seguinte.webp",
    width: 1400,
    quality: 92,
  },
  {
    src: "d8c83cf8-a99f-43e9-8664-58ea2877f0d0/bussola-erro-nunca-foi-voce.png",
    dest: "bussola-erro-nunca-foi-voce.webp",
    width: 1400,
    quality: 92,
  },
  {
    src: "c02baaa4-3ba3-4ee1-b0db-b27b99c855aa/bussola-hero.png",
    dest: "bussola-hero.webp",
    width: 1400,
    quality: 92,
  },
  {
    src: "73ee9d76-5936-47b2-a4bc-b1aa2566ec2f/bussola-hero-mobile.png",
    dest: "bussola-hero-mobile.webp",
    width: 1080,
    quality: 92,
  },
];

async function convertAll() {
  for (const item of filesToConvert) {
    const srcPath = path.join(PUBLIC_DIR, item.src);
    const destPath = path.join(ASSETS_DIR, item.dest);
    if (!fs.existsSync(srcPath)) {
      console.warn(`Aviso: Arquivo não encontrado em ${srcPath}`);
      continue;
    }
    const inputBuf = fs.readFileSync(srcPath);
    const outBuf = await sharp(inputBuf)
      .resize({ width: item.width, withoutEnlargement: true })
      .webp({ quality: item.quality, effort: 6, smartSubsample: true })
      .toBuffer();
    fs.writeFileSync(destPath, outBuf);
    console.log(
      `Convertido: ${item.dest} (${outBuf.length} bytes) <- original (${inputBuf.length} bytes)`,
    );
  }
  console.log("Conversão HD concluída com sucesso!");
}

convertAll();
