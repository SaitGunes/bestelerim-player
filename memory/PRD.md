# Bestelerim Media Player - PRD

## Problem Statement
GitHub'da barındırılan MP3 dosyalarını Railway ile yayınlamak için basit bir medya oynatıcı web sitesi.

## User Persona
- Kendi bestelerini paylaşmak isteyen müzisyen
- Müzik severler

## Core Requirements
- GitHub repo'dan medya dosyalarını çekme
- Audio/Video oynatma
- Koyu tema, profesyonel tasarım
- Responsive tasarım

## What's Been Implemented (December 2025)
- [x] Backend API - GitHub API entegrasyonu
- [x] /api/media - Medya dosyalarını listele
- [x] /api/play/{file_name} - Oynatma istatistikleri
- [x] /api/stats - İstatistik görüntüleme
- [x] Frontend - Koyu temalı müzik oynatıcı
- [x] Sidebar navigasyon
- [x] Şarkı listesi grid görünümü
- [x] Sabit player bar (play/pause, ileri/geri, shuffle, repeat)
- [x] Ses kontrolü
- [x] Favori özelliği
- [x] Mobil responsive tasarım

## GitHub Repo
https://github.com/SaitGunes/bestelerim

## Architecture
- Backend: FastAPI + httpx (GitHub API)
- Frontend: React + TailwindCSS + Shadcn UI
- Database: MongoDB (oynatma istatistikleri için)

## Backlog
- P1: Şarkı sözleri görüntüleme
- P2: Playlist oluşturma
- P2: Şarkı arama
- P3: Karanlık/açık tema geçişi
