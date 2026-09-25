import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import path from 'path'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'serve-local-heritage-data',
      configureServer(server) {
        // Direct local file server for PDF, DOCX, and standardized Markdown
        server.middlewares.use((req, res, next) => {
          const url = req.url || '';
          
          // 1. PDF & Raw file streaming: /api/pdf/* or /api/file/*
          if (url.startsWith('/api/pdf/') || url.startsWith('/api/file/')) {
            const rawFilename = decodeURIComponent(url.replace(/^\/api\/(pdf|file)\//, '').split('#')[0].split('?')[0]);
            const filePath = path.resolve(process.cwd(), '../data/landing/legal', rawFilename);
            if (fs.existsSync(filePath)) {
              const stat = fs.statSync(filePath);
              const ext = path.extname(filePath).toLowerCase();
              const isPdf = ext === '.pdf';
              const contentType = isPdf ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
              res.writeHead(200, {
                'Content-Type': contentType,
                'Content-Length': stat.size,
                'Content-Disposition': isPdf ? `inline; filename="${encodeURIComponent(rawFilename)}"` : `attachment; filename="${encodeURIComponent(rawFilename)}"`,
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache',
              });
              fs.createReadStream(filePath).pipe(res);
              return;
            }
          }

          // 2. Standardized text content: /api/content/:type/:filename
          if (url.startsWith('/api/content/')) {
            const cleanUrl = url.replace(/^\/api\/content\//, '').split('?')[0];
            const slashIndex = cleanUrl.indexOf('/');
            if (slashIndex !== -1) {
              const docType = cleanUrl.substring(0, slashIndex);
              const filename = decodeURIComponent(cleanUrl.substring(slashIndex + 1));
              const stem = path.basename(filename, path.extname(filename));
              const mdPath = path.resolve(process.cwd(), '../data/standardized', docType, `${stem}.md`);
              
              if (fs.existsSync(mdPath)) {
                const content = fs.readFileSync(mdPath, 'utf-8');
                res.writeHead(200, {
                  'Content-Type': 'application/json; charset=utf-8',
                  'Access-Control-Allow-Origin': '*'
                });
                res.end(JSON.stringify({
                  filename,
                  stem,
                  type: docType,
                  content,
                  is_markdown: true
                }));
                return;
              }
            }
          }

          next();
        });
      }
    }
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

