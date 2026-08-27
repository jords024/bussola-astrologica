import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const PUBLIC_DIR = path.resolve('public/__l5e/assets-v1');

function getFiles(dir) {
  let files = [];
  const list = fs.readdirSync(dir);
  for (const item of list) {
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      files = files.concat(getFiles(full));
    } else if (item.endsWith('.png') || item.endsWith('.jpg') || item.endsWith('.jpeg')) {
      files.push(full);
    }
  }
  return files;
}

async function convert() {
  const files = getFiles(PUBLIC_DIR);
  console.log(`Convertendo ${files.length} imagens para WebP ultra-leve...`);

  let totalBefore = 0;
  let totalAfter = 0;

  for (const file of files) {
    const beforeSize = fs.statSync(file).size;
    totalBefore += beforeSize;
    const base = path.basename(file).toLowerCase();
    
    // Dimensões adequadas para desktop e mobile
    let maxWidth = 1000;
    if (base.includes('retrato')) maxWidth = 560;
    else if (base.includes('mobile')) maxWidth = 640;
    else if (base.includes('logo')) maxWidth = 400;
    else if (base.includes('pa')) maxWidth = 300;

    try {
      const inputBuffer = fs.readFileSync(file);
      const metadata = await sharp(inputBuffer).metadata();

      let pipeline = sharp(inputBuffer);
      if (metadata.width && metadata.width > maxWidth) {
        pipeline = pipeline.resize({ width: maxWidth, withoutEnlargement: true });
      }

      // Compactação máxima WebP (ou PNG otimizado)
      // Usamos formato PNG com quantização de 8-bit com dithering suave para manter compatibilidade com extensão de arquivo
      const outputBuffer = await pipeline
        .png({
          quality: 68,
          compressionLevel: 9,
          effort: 10,
          palette: true,
          colors: 128,
        })
        .toBuffer();

      if (outputBuffer.length < beforeSize) {
        fs.writeFileSync(file, outputBuffer);
        totalAfter += outputBuffer.length;
        console.log(`✓ ${path.basename(file)}: ${(beforeSize / 1024).toFixed(0)}KB -> ${(outputBuffer.length / 1024).toFixed(0)}KB (-${Math.round((1 - outputBuffer.length / beforeSize) * 100)}%)`);
      } else {
        totalAfter += beforeSize;
        console.log(`- ${path.basename(file)}: mantido (${(beforeSize / 1024).toFixed(0)}KB)`);
      }
    } catch (err) {
      console.error(`Erro ao processar ${file}:`, err);
      totalAfter += beforeSize;
    }
  }

  console.log(`\n===========================================`);
  console.log(`Tamanho Total Antes: ${(totalBefore / 1024).toFixed(0)} KB`);
  console.log(`Tamanho Total Depois: ${(totalAfter / 1024).toFixed(0)} KB`);
  console.log(`Economia: -${Math.round((1 - totalAfter / totalBefore) * 100)}%!`);
  console.log(`===========================================`);
}

convert();
