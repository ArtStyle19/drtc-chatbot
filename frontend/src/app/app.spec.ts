import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('renders the primary navigation and the corpus notice', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;

    const links = [...element.querySelectorAll('nav a')].map((a) => a.textContent?.trim());
    expect(links).toEqual(['Consultas', 'Biblioteca']);
    expect(element.querySelector('[role="note"]')?.textContent).toContain('Corpus de prueba');
  });
});
