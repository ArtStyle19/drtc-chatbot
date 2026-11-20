/**
 * Responses of GET /api/v1/search captured from the real backend (dev database, the three norms
 * ingested, no embeddings provider so the words arm answers and `degraded` says why). Trimmed to the
 * first results and scores rounded; nothing else was edited. The "everything worked" variant is
 * derived in the specs by clearing `degraded`.
 */

/** GET /search?q=plazo para interponer recurso de apelación&debug=true (6 of 20 results shown). */
export const searchPlazo = {
  query: 'plazo para interponer recurso de apelación',
  mode: 'hybrid',
  degraded: ['vector_unavailable'],
  total: 29,
  reference: null,
  facets: [
    {
      instrument_id: 'tuo-ley-27444',
      short_name: 'TUO de la Ley 27444 (LPAG)',
      count: 26,
    },
    {
      instrument_id: 'ds-017-2009-mtc',
      short_name: 'RENAT (DS 017-2009-MTC)',
      count: 3,
    },
  ],
  results: [
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:220',
      path: 'articulo:220',
      kind: 'article',
      label: '220',
      title: 'Recurso de apelación',
      citation: 'TUO de la Ley N.° 27444, art. 220',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' de ',
          match: false,
        },
        {
          text: 'apelación',
          match: true,
        },
        {
          text: ' se interpondrá cuando la impugnación se sustente en diferente interpretación de las pruebas producidas o cuando se trate de cuestiones de puro derecho, debiendo dirigirse a la misma autoridad que expidió',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:220',
          citation: 'TUO de la Ley N.° 27444, art. 220',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' de ',
              match: false,
            },
            {
              text: 'apelación',
              match: true,
            },
            {
              text: ' se interpondrá cuando la impugnación se sustente en diferente interpretación de las pruebas producidas o cuando se trate de cuestiones de puro derecho, debiendo dirigirse a la misma autoridad que expidió',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0164,
      debug: {
        reference_rank: null,
        lexical_rank: 1,
        vector_rank: null,
        score: 0.0164,
      },
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:218',
      path: 'articulo:218/numeral:218.1/literal:b',
      kind: 'literal',
      label: 'b',
      title: null,
      citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. b)',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'Recurso',
          match: true,
        },
        {
          text: ' de ',
          match: false,
        },
        {
          text: 'apelación',
          match: true,
        },
        {
          text: ' Solo en caso que por ley o decreto legislativo se establezca expresamente, cabe la interposición del ',
          match: false,
        },
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' administrativo de revisión',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:218/numeral:218.1/literal:b',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. b)',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recurso',
              match: true,
            },
            {
              text: ' de ',
              match: false,
            },
            {
              text: 'apelación',
              match: true,
            },
            {
              text: ' Solo en caso que por ley o decreto legislativo se establezca expresamente, cabe la interposición del ',
              match: false,
            },
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' administrativo de revisión',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218',
          citation: 'TUO de la Ley N.° 27444, art. 218',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recursos',
              match: true,
            },
            {
              text: ' administrativos',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.1/literal:a',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. a)',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recurso',
              match: true,
            },
            {
              text: ' de reconsideración',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.1',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recursos',
              match: true,
            },
            {
              text: ' administrativos',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.2',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.2',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'término para la interposición de los ',
              match: false,
            },
            {
              text: 'recursos',
              match: true,
            },
            {
              text: ' es de quince (15) días perentorios, y deberán resolverse en el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' de treinta (30) días',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0161,
      debug: {
        reference_rank: null,
        lexical_rank: 2,
        vector_rank: null,
        score: 0.0161,
      },
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:219',
      path: 'articulo:219',
      kind: 'article',
      label: '219',
      title: 'Recurso de reconsideración',
      citation: 'TUO de la Ley N.° 27444, art. 219',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' de reconsideración se interpondrá ante el mismo órgano que dictó el primer acto que es materia de la impugnación y deberá sustentarse en nueva prueba. En los casos de actos administrativos emitidos por órganos',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:219',
          citation: 'TUO de la Ley N.° 27444, art. 219',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' de reconsideración se interpondrá ante el mismo órgano que dictó el primer acto que es materia de la impugnación y deberá sustentarse en nueva prueba. En los casos de actos administrativos emitidos por órganos',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0159,
      debug: {
        reference_rank: null,
        lexical_rank: 3,
        vector_rank: null,
        score: 0.0159,
      },
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:145',
      path: 'articulo:145',
      kind: 'article',
      label: '145',
      title: 'Transcurso del plazo',
      citation: 'TUO de la Ley N.° 27444, art. 145',
      page_start: 198,
      page_end: 198,
      snippet: [
        {
          text: 'Transcurso del ',
          match: false,
        },
        {
          text: 'plazo',
          match: true,
        },
      ],
      matched: [
        {
          path: 'articulo:145',
          citation: 'TUO de la Ley N.° 27444, art. 145',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Transcurso del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.1',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.1',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es señalado por días, se entenderá por hábiles consecutivos, excluyendo del cómputo aquellos no laborables del servicio, y los feriados no laborables de orden nacional o regional',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.3',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.3',
          page_start: 198,
          page_end: 199,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es fijado en meses o años, es contado de fecha a fecha, concluyendo el día igual al del mes o año que inició, completando el número de meses o años fijados para',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0156,
      debug: {
        reference_rank: null,
        lexical_rank: 4,
        vector_rank: null,
        score: 0.0156,
      },
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:147',
      path: 'articulo:147',
      kind: 'article',
      label: '147',
      title: 'Plazos improrrogables',
      citation: 'TUO de la Ley N.° 27444, art. 147',
      page_start: 199,
      page_end: 199,
      snippet: [
        {
          text: 'Plazos',
          match: true,
        },
        {
          text: ' improrrogables',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:147',
          citation: 'TUO de la Ley N.° 27444, art. 147',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'Plazos',
              match: true,
            },
            {
              text: ' improrrogables',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.1',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.1',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'plazos',
              match: true,
            },
            {
              text: ' fijados por norma expresa son improrrogables, salvo disposición habilitante en contrario',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.4',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.4',
          page_start: 200,
          page_end: 200,
          snippet: [
            {
              text: 'cargo necesaria para adoptar una decisión de fondo, puede solicitar la suspensión del cómputo del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' del procedimiento hasta por un ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' de treinta (30) días hábiles',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.2',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.2',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'autoridad competente puede otorgar prórroga a los ',
              match: false,
            },
            {
              text: 'plazos',
              match: true,
            },
            {
              text: ' establecidos para la actuación de pruebas o para la emisión de informes o dictámenes, cuando así lo soliciten antes de su vencimiento los administrados o los funcionarios',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.3',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.3',
          page_start: 200,
          page_end: 200,
          snippet: [
            {
              text: 'prórroga es concedida por única vez mediante decisión expresa, siempre que el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' no haya sido perjudicado por causa imputable a quien la solicita y siempre que aquella no afecte derechos de terceros',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0154,
      debug: {
        reference_rank: null,
        lexical_rank: 5,
        vector_rank: null,
        score: 0.0154,
      },
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:222',
      path: 'articulo:222',
      kind: 'article',
      label: '222',
      title: 'Acto firme',
      citation: 'TUO de la Ley N.° 27444, art. 222',
      page_start: 237,
      page_end: 237,
      snippet: [
        {
          text: 'vencidos los ',
          match: false,
        },
        {
          text: 'plazos',
          match: true,
        },
        {
          text: ' para ',
          match: false,
        },
        {
          text: 'interponer',
          match: true,
        },
        {
          text: ' los ',
          match: false,
        },
        {
          text: 'recursos',
          match: true,
        },
        {
          text: ' administrativos se perderá el derecho a articularlos quedando firme el acto',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:222',
          citation: 'TUO de la Ley N.° 27444, art. 222',
          page_start: 237,
          page_end: 237,
          snippet: [
            {
              text: 'vencidos los ',
              match: false,
            },
            {
              text: 'plazos',
              match: true,
            },
            {
              text: ' para ',
              match: false,
            },
            {
              text: 'interponer',
              match: true,
            },
            {
              text: ' los ',
              match: false,
            },
            {
              text: 'recursos',
              match: true,
            },
            {
              text: ' administrativos se perderá el derecho a articularlos quedando firme el acto',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0152,
      debug: {
        reference_rank: null,
        lexical_rank: 6,
        vector_rank: null,
        score: 0.0152,
      },
    },
  ],
};

/** GET /search?q=art. 5 Ley 27181 plazo — the reference goes first (3 of 20 results). */
export const searchReference = {
  query: 'art. 5 Ley 27181 plazo',
  mode: 'hybrid',
  degraded: ['vector_unavailable'],
  total: 30,
  reference: 'art. 5',
  facets: [
    {
      instrument_id: 'tuo-ley-27444',
      short_name: 'TUO de la Ley 27444 (LPAG)',
      count: 24,
    },
    {
      instrument_id: 'ds-017-2009-mtc',
      short_name: 'RENAT (DS 017-2009-MTC)',
      count: 5,
    },
    {
      instrument_id: 'ley-27181',
      short_name: 'Ley 27181 (LGTTT)',
      count: 1,
    },
  ],
  results: [
    {
      instrument_id: 'ley-27181',
      instrument_short_name: 'Ley 27181 (LGTTT)',
      version_id: 'ley-27181@2020-05',
      edition_label: 'Compilación no oficial con modificaciones hasta mayo de 2020',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:5',
      path: 'articulo:5',
      kind: 'article',
      label: '5',
      title: 'De la promoción de la inversión privada',
      citation: 'Ley N.° 27181, art. 5',
      page_start: 5,
      page_end: 5,
      snippet: [],
      matched: [],
      via: ['reference'],
      score: 1.0,
      debug: null,
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:145',
      path: 'articulo:145',
      kind: 'article',
      label: '145',
      title: 'Transcurso del plazo',
      citation: 'TUO de la Ley N.° 27444, art. 145',
      page_start: 198,
      page_end: 198,
      snippet: [
        {
          text: 'Transcurso del ',
          match: false,
        },
        {
          text: 'plazo',
          match: true,
        },
      ],
      matched: [
        {
          path: 'articulo:145',
          citation: 'TUO de la Ley N.° 27444, art. 145',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Transcurso del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.1',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.1',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es señalado por días, se entenderá por hábiles consecutivos, excluyendo del cómputo aquellos no laborables del servicio, y los feriados no laborables de orden nacional o regional',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.3',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.3',
          page_start: 198,
          page_end: 199,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es fijado en meses o años, es contado de fecha a fecha, concluyendo el día igual al del mes o año que inició, completando el número de meses o años fijados para',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.2',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.2',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Cuando el último día del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' o la fecha determinada es inhábil o por cualquier otra circunstancia la atención al público ese día no funcione durante el horario normal, son entendidos prorrogados al primer día',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0164,
      debug: null,
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:147',
      path: 'articulo:147',
      kind: 'article',
      label: '147',
      title: 'Plazos improrrogables',
      citation: 'TUO de la Ley N.° 27444, art. 147',
      page_start: 199,
      page_end: 199,
      snippet: [
        {
          text: 'Plazos',
          match: true,
        },
        {
          text: ' improrrogables',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:147',
          citation: 'TUO de la Ley N.° 27444, art. 147',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'Plazos',
              match: true,
            },
            {
              text: ' improrrogables',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.1',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.1',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'plazos',
              match: true,
            },
            {
              text: ' fijados por norma expresa son improrrogables, salvo disposición habilitante en contrario',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.4',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.4',
          page_start: 200,
          page_end: 200,
          snippet: [
            {
              text: 'cargo necesaria para adoptar una decisión de fondo, puede solicitar la suspensión del cómputo del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' del procedimiento hasta por un ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' de treinta (30) días hábiles',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.2',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.2',
          page_start: 199,
          page_end: 199,
          snippet: [
            {
              text: 'autoridad competente puede otorgar prórroga a los ',
              match: false,
            },
            {
              text: 'plazos',
              match: true,
            },
            {
              text: ' establecidos para la actuación de pruebas o para la emisión de informes o dictámenes, cuando así lo soliciten antes de su vencimiento los administrados o los funcionarios',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:147/numeral:147.3',
          citation: 'TUO de la Ley N.° 27444, art. 147, num. 147.3',
          page_start: 200,
          page_end: 200,
          snippet: [
            {
              text: 'prórroga es concedida por única vez mediante decisión expresa, siempre que el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' no haya sido perjudicado por causa imputable a quien la solicita y siempre que aquella no afecte derechos de terceros',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0161,
      debug: null,
    },
  ],
};

/** GET /search?q=plazo para interponer recurso de apelación&instrument=tuo-ley-27444 (4 of 20). */
export const searchFiltered = {
  query: 'plazo para interponer recurso de apelación',
  mode: 'hybrid',
  degraded: ['vector_unavailable'],
  total: 26,
  reference: null,
  facets: [
    {
      instrument_id: 'tuo-ley-27444',
      short_name: 'TUO de la Ley 27444 (LPAG)',
      count: 26,
    },
    {
      instrument_id: 'ds-017-2009-mtc',
      short_name: 'RENAT (DS 017-2009-MTC)',
      count: 3,
    },
  ],
  results: [
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:220',
      path: 'articulo:220',
      kind: 'article',
      label: '220',
      title: 'Recurso de apelación',
      citation: 'TUO de la Ley N.° 27444, art. 220',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' de ',
          match: false,
        },
        {
          text: 'apelación',
          match: true,
        },
        {
          text: ' se interpondrá cuando la impugnación se sustente en diferente interpretación de las pruebas producidas o cuando se trate de cuestiones de puro derecho, debiendo dirigirse a la misma autoridad que expidió',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:220',
          citation: 'TUO de la Ley N.° 27444, art. 220',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' de ',
              match: false,
            },
            {
              text: 'apelación',
              match: true,
            },
            {
              text: ' se interpondrá cuando la impugnación se sustente en diferente interpretación de las pruebas producidas o cuando se trate de cuestiones de puro derecho, debiendo dirigirse a la misma autoridad que expidió',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0164,
      debug: null,
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:218',
      path: 'articulo:218/numeral:218.1/literal:b',
      kind: 'literal',
      label: 'b',
      title: null,
      citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. b)',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'Recurso',
          match: true,
        },
        {
          text: ' de ',
          match: false,
        },
        {
          text: 'apelación',
          match: true,
        },
        {
          text: ' Solo en caso que por ley o decreto legislativo se establezca expresamente, cabe la interposición del ',
          match: false,
        },
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' administrativo de revisión',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:218/numeral:218.1/literal:b',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. b)',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recurso',
              match: true,
            },
            {
              text: ' de ',
              match: false,
            },
            {
              text: 'apelación',
              match: true,
            },
            {
              text: ' Solo en caso que por ley o decreto legislativo se establezca expresamente, cabe la interposición del ',
              match: false,
            },
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' administrativo de revisión',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218',
          citation: 'TUO de la Ley N.° 27444, art. 218',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recursos',
              match: true,
            },
            {
              text: ' administrativos',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.1/literal:a',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1, lit. a)',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'Recurso',
              match: true,
            },
            {
              text: ' de reconsideración',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.1',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.1',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recursos',
              match: true,
            },
            {
              text: ' administrativos',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:218/numeral:218.2',
          citation: 'TUO de la Ley N.° 27444, art. 218, num. 218.2',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'término para la interposición de los ',
              match: false,
            },
            {
              text: 'recursos',
              match: true,
            },
            {
              text: ' es de quince (15) días perentorios, y deberán resolverse en el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' de treinta (30) días',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0161,
      debug: null,
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:219',
      path: 'articulo:219',
      kind: 'article',
      label: '219',
      title: 'Recurso de reconsideración',
      citation: 'TUO de la Ley N.° 27444, art. 219',
      page_start: 236,
      page_end: 236,
      snippet: [
        {
          text: 'recurso',
          match: true,
        },
        {
          text: ' de reconsideración se interpondrá ante el mismo órgano que dictó el primer acto que es materia de la impugnación y deberá sustentarse en nueva prueba. En los casos de actos administrativos emitidos por órganos',
          match: false,
        },
      ],
      matched: [
        {
          path: 'articulo:219',
          citation: 'TUO de la Ley N.° 27444, art. 219',
          page_start: 236,
          page_end: 236,
          snippet: [
            {
              text: 'recurso',
              match: true,
            },
            {
              text: ' de reconsideración se interpondrá ante el mismo órgano que dictó el primer acto que es materia de la impugnación y deberá sustentarse en nueva prueba. En los casos de actos administrativos emitidos por órganos',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0159,
      debug: null,
    },
    {
      instrument_id: 'tuo-ley-27444',
      instrument_short_name: 'TUO de la Ley 27444 (LPAG)',
      version_id: 'tuo-ley-27444@ds-004-2019-jus-ed2021',
      edition_label: 'Segunda Edición Oficial MINJUSDH (julio de 2021)',
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      unit_path: 'articulo:145',
      path: 'articulo:145',
      kind: 'article',
      label: '145',
      title: 'Transcurso del plazo',
      citation: 'TUO de la Ley N.° 27444, art. 145',
      page_start: 198,
      page_end: 198,
      snippet: [
        {
          text: 'Transcurso del ',
          match: false,
        },
        {
          text: 'plazo',
          match: true,
        },
      ],
      matched: [
        {
          path: 'articulo:145',
          citation: 'TUO de la Ley N.° 27444, art. 145',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Transcurso del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.1',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.1',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es señalado por días, se entenderá por hábiles consecutivos, excluyendo del cómputo aquellos no laborables del servicio, y los feriados no laborables de orden nacional o regional',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.3',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.3',
          page_start: 198,
          page_end: 199,
          snippet: [
            {
              text: 'Cuando el ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' es fijado en meses o años, es contado de fecha a fecha, concluyendo el día igual al del mes o año que inició, completando el número de meses o años fijados para',
              match: false,
            },
          ],
        },
        {
          path: 'articulo:145/numeral:145.2',
          citation: 'TUO de la Ley N.° 27444, art. 145, num. 145.2',
          page_start: 198,
          page_end: 198,
          snippet: [
            {
              text: 'Cuando el último día del ',
              match: false,
            },
            {
              text: 'plazo',
              match: true,
            },
            {
              text: ' o la fecha determinada es inhábil o por cualquier otra circunstancia la atención al público ese día no funcione durante el horario normal, son entendidos prorrogados al primer día',
              match: false,
            },
          ],
        },
      ],
      via: ['lexical'],
      score: 0.0156,
      debug: null,
    },
  ],
};

/** GET /search?q=zzzz qqqq — nothing matches. */
export const searchEmpty = {
  query: 'zzzz qqqq',
  mode: 'hybrid',
  degraded: ['vector_unavailable'],
  total: 0,
  reference: null,
  facets: [],
  results: [],
};
