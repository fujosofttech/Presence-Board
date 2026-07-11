import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(__dirname, '../static/index.html');
const dest = path.resolve(__dirname, '../templates/index.html');

if (fs.existsSync(src)) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(src, dest);
  console.log('Moved index.html to templates/');
} else {
  console.error('Source index.html not found:', src);
}
