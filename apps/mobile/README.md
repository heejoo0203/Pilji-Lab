# 필지랩 Android Wrapper

## Overview
- app name: `필지랩`
- package id: `com.autolv.app`
- source URL: `https://auto-lv.vercel.app`
- icon source: `docs/assets/brand/mobile-icon.jpg`

## Setup
```bash
cd apps/mobile
npm install
npx cap sync android
```

필수 환경:
- JDK 21
- Android SDK Platform 35

## Build
Debug:
```bash
cd apps/mobile
npm run android:build:debug
```

Release:
```bash
cd apps/mobile
npm run android:build:release
```

환경변수:
- `AUTOLV_UPLOAD_STORE_FILE`
- `AUTOLV_UPLOAD_STORE_PASSWORD`
- `AUTOLV_UPLOAD_KEY_ALIAS`
- `AUTOLV_UPLOAD_KEY_PASSWORD`
