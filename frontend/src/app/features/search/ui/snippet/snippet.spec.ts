import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { SearchSegment } from '../../../../core/api/models';
import { Snippet } from './snippet';

@Component({
  imports: [Snippet],
  template: '<drtc-snippet [segments]="segments" />',
})
class Host {
  segments: SearchSegment[] = [];
}

function render(segments: SearchSegment[]): HTMLElement {
  const fixture = TestBed.createComponent(Host);
  fixture.componentInstance.segments = segments;
  fixture.detectChanges();
  return fixture.nativeElement.querySelector('drtc-snippet') as HTMLElement;
}

describe('Snippet', () => {
  it('writes the text exactly as given, with the spaces around the marked words', () => {
    const el = render([
      { text: 'El plazo de ', match: false },
      { text: 'quince', match: true },
      { text: ' días hábiles', match: false },
    ]);

    expect(el.textContent).toBe('El plazo de quince días hábiles');
  });

  it('marks only the matched segments', () => {
    const el = render([
      { text: 'a ', match: false },
      { text: 'uno', match: true },
      { text: ' b ', match: false },
      { text: 'dos', match: true },
    ]);

    expect([...el.querySelectorAll('mark')].map((m) => m.textContent)).toEqual(['uno', 'dos']);
  });

  it('shows markup in the text as plain text: it can never become elements', () => {
    const el = render([
      { text: '<img src=x onerror=alert(1)> ', match: false },
      { text: '<b>silencio</b> & más', match: true },
    ]);

    expect(el.querySelector('img')).toBeNull();
    expect(el.querySelector('b')).toBeNull();
    expect(el.textContent).toBe('<img src=x onerror=alert(1)> <b>silencio</b> & más');
    expect(el.querySelector('mark')?.textContent).toBe('<b>silencio</b> & más');
  });

  it('renders nothing for an empty list', () => {
    expect(render([]).textContent).toBe('');
  });
});
