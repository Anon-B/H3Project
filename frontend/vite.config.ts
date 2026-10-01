import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins:[react()],
  server:{host:'0.0.0.0',port:5173},
  build:{
    target:'es2022',
    sourcemap:false,
    chunkSizeWarningLimit:1300,
    rollupOptions:{
      onwarn(warn, handler){
        if (warn.message.includes('contains an annotation that Rollup cannot interpret') && String(warn.id||'').includes('/node_modules/zod/')) return;
        handler(warn);
      },
      output:{
        manualChunks(id){
          if (!id.includes('node_modules')) return;
          if (id.includes('maplibre-gl') || id.includes('maplibre-gl-draw')) return 'maplibre';
          if (id.includes('@deck.gl') || id.includes('@luma.gl') || id.includes('@loaders.gl')) return 'deckgl';
          if (id.includes('h3-js')) return 'h3';
          if (id.includes('@mui') || id.includes('@emotion')) return 'mui';
        }
      }
    }
  }
});
