import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@pages': '/src/pages',
      '@services': '/src/services',
      '@hooks': '/src/hooks',
      '@utils': '/src/utils',
      '@types': '/src/types',
      '@stores': '/src/stores',
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      // 日志管理API路由到FastAPI服务
      '/api/v1/logs': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      // 其他FastAPI端点
      '/api/v1/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/status': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/metrics': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/cache': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/system': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/executions': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      // 默认API路由到Django服务
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8001',  // ✅ 迁移到 FastAPI 服务
        ws: true,
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'utils': ['axios', 'dayjs', 'lodash']
        }
      }
    }
  }
})
