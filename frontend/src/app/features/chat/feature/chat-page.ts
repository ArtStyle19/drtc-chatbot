import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

interface PlannedStep {
  readonly title: string;
  readonly description: string;
}

/** Placeholder of the Consultas feature until spec 005 (cited answers) is delivered. */
@Component({
  selector: 'drtc-chat-page',
  imports: [RouterLink],
  templateUrl: './chat-page.html',
})
export class ChatPage {
  protected readonly steps: readonly PlannedStep[] = [
    {
      title: 'Pregunte con sus palabras',
      description: 'Por ejemplo: «¿Cuál es el plazo para interponer un recurso de apelación?».',
    },
    {
      title: 'Reciba una respuesta fundamentada',
      description:
        'Conclusión, fundamento jurídico, análisis y excepciones, con cada afirmación citada.',
    },
    {
      title: 'Verifique en la fuente',
      description:
        'Cada cita abre la página exacta del PDF con el pasaje resaltado y su sello de vigencia.',
    },
  ];
}
