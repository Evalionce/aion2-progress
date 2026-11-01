import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../public');
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
export function fileForUrl(url) {
  const pathname = decodeURIComponent(new URL(url, 'http://localhost').pathname);
  const file = resolve(root, '.' + pathname + (pathname.endsWith('/') ? 'index.html' : ''));
  if (!file.startsWith(root + sep)) throw new Error('Outside public directory');
  return file;
}
export function createAppServer() {
  return createServer(async (request, response) => {
    if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405).end(); return; }
    try {
      const file = fileForUrl(request.url);
      const bytes = await readFile(file);
      response.writeHead(200, {'Content-Type':types[extname(file)] ?? 'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
      response.end(request.method === 'HEAD' ? undefined : bytes);
    } catch {
      response.writeHead(404, {'Content-Type':'text/plain; charset=utf-8'}).end('Not found');
    }
  });
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 4173);
  createAppServer().listen(port, '127.0.0.1', () => console.log(`AION 2: http://127.0.0.1:${port}/`));
}
