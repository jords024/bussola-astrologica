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

async function optimize() {
  const files = getFiles(PUBLIC_DIR);
  console.log(`Otimizando agressivamente ${files.length} imagens para nota máxima no PageSpeed...`);

  let totalBefore = 0;
  let totalAfter = 0;

  for (const file of files) {
    const beforeSize = fs.statSync(file).size;
    totalBefore += beforeSize;
    const base = path.basename(file).toLowerCase();
    const isMobile = base.includes('mobile') || base.includes('pa') || base.includes('logo');
    const maxWidth = isMobile ? 800 : 1200;

    try {
      const inputBuffer = fs.readFileSync(file);
      const metadata = await sharp(inputBuffer).metadata();

      let pipeline = sharp(inputBuffer);
      if (metadata.width && metadata.width > maxWidth) {
        pipeline = pipeline.resize({ width: maxWidth, withoutEnlargement: true });
      }

      // Converte internamente para PNG quantizado otimizado (palette 256 cores, compression 9)
      const outputBuffer = await pipeline
        .png({
          quality: 72,
          compressionLevel: 9,
          effort: 10,
          palette: true,
          dither: 0.8,
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
      console.error(`Erro ao otimizar ${file}:`, err);
      totalAfter += beforeSize;
    }
  }

  console.log(`\n===========================================`);
  console.log(`Tamanho Total Antes: ${(totalBefore / (1024 * 1024)).toFixed(2)} MB`);
  console.log(`Tamanho Total Depois: ${(totalAfter / (1024 * 1024)).toFixed(2)} MB`);
  console.log(`Economia adicional: -${Math.round((1 - totalAfter / totalBefore) * 100)}%!`);
  console.log(`===========================================`);
}

optimize();
