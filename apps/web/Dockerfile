# apps/web/Dockerfile
# Next.js Frontend Container

# ============================================================
# BASE STAGE - Common setup
# ============================================================
FROM node:20-alpine AS base

# Install dependencies for node-gyp (some packages need it)
RUN apk add --no-cache libc6-compat

WORKDIR /app

# ============================================================
# DEPENDENCIES STAGE - Install all dependencies
# ============================================================
FROM base AS deps

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# ============================================================
# DEVELOPMENT STAGE - For local development with hot reload
# ============================================================
FROM base AS development

WORKDIR /app

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Expose port 3000
EXPOSE 3000

# Set environment
ENV NODE_ENV=development
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start development server
CMD ["npm", "run", "dev"]

# ============================================================
# BUILD STAGE - Build the production application
# ============================================================
FROM base AS builder

WORKDIR /app

# Copy node_modules and source
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set production environment for build
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# ============================================================
# PRODUCTION STAGE - Minimal production image
# ============================================================
FROM base AS production

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built assets from builder
COPY --from=builder /app/public ./public

# Copy the standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
