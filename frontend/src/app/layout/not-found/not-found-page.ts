import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'drtc-not-found-page',
  imports: [RouterLink],
  template: `
    <section class="mx-auto max-w-2xl px-6 py-20 text-center">
      <p class="font-mono text-sm text-text-tertiary">Error 404</p>
      <h1 class="mt-2 font-serif text-2xl text-ink-900">No encontramos esta página</h1>
      <p class="mt-3 text-text-secondary">
        Es posible que la dirección esté mal escrita o que la sección aún no exista.
      </p>
      <a routerLink="/biblioteca" class="mt-6 inline-block font-semibold text-ink-600 underline">
        Ir a la Biblioteca normativa
      </a>
    </section>
  `,
})
export class NotFoundPage {}
