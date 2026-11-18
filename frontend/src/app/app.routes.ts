import { Routes } from '@angular/router';

/** Feature routes are lazy-loaded; each feature folder stays self-contained (ADR-0008). */
export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'biblioteca' },
  {
    path: 'biblioteca',
    title: 'Biblioteca normativa · DRTC Puno',
    loadComponent: () =>
      import('./features/library/feature/library-page').then((m) => m.LibraryPage),
  },
  {
    // No static `title`: the page sets it from the norm and the provision being read.
    path: 'biblioteca/:norma',
    loadComponent: () => import('./features/reader/feature/reader-page').then((m) => m.ReaderPage),
  },
  {
    path: 'consultas',
    title: 'Consultas · DRTC Puno',
    loadComponent: () => import('./features/chat/feature/chat-page').then((m) => m.ChatPage),
  },
  {
    path: '**',
    title: 'Página no encontrada · DRTC Puno',
    loadComponent: () => import('./layout/not-found/not-found-page').then((m) => m.NotFoundPage),
  },
];
