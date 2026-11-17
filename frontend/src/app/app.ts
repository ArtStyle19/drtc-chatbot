import { Component } from '@angular/core';

import { AppShell } from './layout/app-shell/app-shell';

@Component({
  selector: 'drtc-root',
  imports: [AppShell],
  template: '<drtc-app-shell />',
})
export class App {}
