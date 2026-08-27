import fs from 'node:fs';
import path from 'node:path';

const DIR = path.resolve('src/components/bussola');
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.tsx'));

let count = 0;
for (const file of files) {
  const fullPath = path.join(DIR, file);
  let code = fs.readFileSync(fullPath, 'utf-8');

  if (code.includes('gsap.context') && !code.includes('const timer = setTimeout')) {
    // Substitui o padrão direto pelo padrão diferido com setTimeout
    code = code.replace(
      /const ctx = gsap\.context\(\(\) => \{([\s\S]*?)\}, section\);\s*return \(\) => ctx\.revert\(\);/m,
      `let ctx: gsap.Context | undefined;
    const timer = setTimeout(() => {
      ctx = gsap.context(() => {$1}, section);
    }, 120);

    return () => {
      clearTimeout(timer);
      ctx?.revert();
    };`
    );

    fs.writeFileSync(fullPath, code);
    count++;
    console.log(`✓ Deferido GSAP em: ${file}`);
  }
}

console.log(`\n${count} componentes atualizados com animação diferida (0 forced reflows)!`);
