import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LucideLibrary, LucideMessagesSquare } from '@lucide/angular';

import { ReferenceSearch } from '../../features/lookup/feature/reference-search';

/** Application frame: identity, primary navigation, corpus status notice and footer. */
@Component({
  selector: 'drtc-app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    LucideLibrary,
    LucideMessagesSquare,
    ReferenceSearch,
  ],
  templateUrl: './app-shell.html',
  styleUrl: './app-shell.css',
})
export class AppShell {}
