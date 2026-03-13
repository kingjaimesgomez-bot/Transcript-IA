// ═══════════════════════════════════════════════════
// TRANSCRIPT IA — ENGINE
// Análisis con Claude API + MusicXML en el navegador
// ═══════════════════════════════════════════════════

// ── Estado global ──────────────────────────────────
let currentAnalysis = null;
let currentFile = null;
let apiKey = localStorage.getItem('tia_apikey') || '';

// ── Modal de API Key ────────────────────────────────
function showApiKeyModal(callback) {
  const existing = document.getElementById('apiKeyModal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'apiKeyModal';
  modal.style.cssText = `
    position:fixed;inset:0;z-index:9999;
    background:rgba(6,6,8,.92);backdrop-filter:blur(10px);
    display:flex;align-items:center;justify-content:center;padding:20px;
  `;
  modal.innerHTML = `
    <div style="background:#0f0f14;border:1px solid rgba(0,255,135,.2);padding:40px;max-width:480px;width:100%;">
      <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#fff;margin-bottom:8px;">
        🔑 API Key de Claude
      </div>
      <p style="font-size:11px;color:#48485a;letter-spacing:1px;margin-bottom:24px;line-height:1.8;">
        Necesitas una API key de Anthropic para analizar canciones.<br>
        Consíguela gratis en <a href="https://console.anthropic.com" target="_blank" style="color:#00ff87;">console.anthropic.com</a>
      </p>
      <input id="apiKeyInput" type="password" placeholder="sk-ant-api03-..." 
        value="${apiKey}"
        style="width:100%;background:#060608;border:1px solid rgba(0,255,135,.2);
        color:#edeae0;font-family:monospace;font-size:13px;padding:14px;
        outline:none;margin-bottom:16px;"/>
      <div style="display:flex;gap:12px;">
        <button onclick="saveApiKey()" style="flex:1;background:#00ff87;border:none;
          color:#000;font-family:'Syne',sans-serif;font-weight:800;font-size:13px;
          letter-spacing:2px;padding:14px;cursor:pointer;">
          GUARDAR Y ANALIZAR
        </button>
        <button onclick="document.getElementById('apiKeyModal').remove()" 
          style="background:none;border:1px solid #1c1c24;color:#48485a;
          font-family:'Syne',sans-serif;font-size:13px;padding:14px 20px;cursor:pointer;">
          CANCELAR
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  document.getElementById('apiKeyInput').focus();
  window._apiKeyCallback = callback;
}

function saveApiKey() {
  const key = document.getElementById('apiKeyInput').value.trim();
  if (!key.startsWith('sk-ant')) {
    alert('API key inválida. Debe empezar con sk-ant-');
    return;
  }
  apiKey = key;
  localStorage.setItem('tia_apikey', key);
  document.getElementById('apiKeyModal').remove();
  if (window._apiKeyCallback) window._apiKeyCallback();
}

// ── Modal de progreso ───────────────────────────────
function showProgress(msg) {
  let modal = document.getElementById('progressModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'progressModal';
    modal.style.cssText = `
      position:fixed;inset:0;z-index:9998;
      background:rgba(6,6,8,.88);backdrop-filter:blur(8px);
      display:flex;align-items:center;justify-content:center;
    `;
    modal.innerHTML = `
      <div style="text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:20px;animation:spin 1s linear infinite;">⟳</div>
        <div id="progressMsg" style="font-family:'IBM Plex Mono',monospace;font-size:13px;
          color:#00ff87;letter-spacing:2px;"></div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  document.getElementById('progressMsg').textContent = msg;
}

function hideProgress() {
  const m = document.getElementById('progressModal');
  if (m) m.remove();
}

// ── Leer archivo como base64 ────────────────────────
function fileToBase64(file) {
  return new Promise((res, rej) => {
    const reader = new FileReader();
    reader.onload = () => res(reader.result.split(',')[1]);
    reader.onerror = rej;
    reader.readAsDataURL(file);
  });
}

// ── Analizar con Claude ─────────────────────────────
async function analyzeWithClaude(file) {
  showProgress('Leyendo archivo de audio...');

  const base64 = await fileToBase64(file);
  const ext = file.name.split('.').pop().toLowerCase();
  const mediaTypes = {
    mp3: 'audio/mpeg', wav: 'audio/wav', flac: 'audio/flac',
    aac: 'audio/aac', ogg: 'audio/ogg', m4a: 'audio/mp4'
  };
  const mediaType = mediaTypes[ext] || 'audio/mpeg';

  showProgress('Enviando a Claude AI para análisis...');

  const systemPrompt = `Eres un arreglista musical experto. Analiza el audio y responde ÚNICAMENTE con JSON válido (sin texto adicional, sin backticks) con esta estructura exacta:
{
  "titulo": "nombre de la canción",
  "tonalidad": "C major",
  "tempo": 120,
  "compas": "4/4",
  "genero": "Pop",
  "duracion_total": "3:45",
  "estructura": [
    {"seccion": "Intro", "compases": "1-8", "descripcion": "descripción detallada"}
  ],
  "instrumentos": [
    {
      "nombre": "Piano",
      "midi_program": 0,
      "rango": "C3-C6",
      "secciones": [
        {
          "nombre": "Intro",
          "descripcion": "descripción",
          "patron": "Am - F - C - G",
          "tecnicas": ["arpegio"],
          "notas_destacadas": ["A3","C4","E4"],
          "notas_musicxml": [
            {"pitch": 69, "duracion": 1.0, "compas": 1},
            {"pitch": 72, "duracion": 0.5, "compas": 1}
          ]
        }
      ]
    }
  ],
  "armonia": {
    "progresion_principal": "Am - F - C - G",
    "progresion_coro": "F - G - Am - Em",
    "modulaciones": [],
    "modo": "Eolio"
  },
  "produccion": {
    "efectos": ["reverb en voz"],
    "dinamica": "mp a mf"
  },
  "notas_arreglista": "observaciones importantes"
}
Para notas_musicxml usa MIDI pitch numbers (60=C4, 69=A4) y duracion en beats (1.0=negra, 0.5=corchea, 2.0=blanca, 4.0=redonda). Incluye al menos 16 notas por instrumento por sección.`;

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true'
    },
    body: JSON.stringify({
      model: 'claude-opus-4-5',
      max_tokens: 4096,
      system: systemPrompt,
      messages: [{
        role: 'user',
        content: [{
          type: 'document',
          source: { type: 'base64', media_type: mediaType, data: base64 }
        }, {
          type: 'text',
          text: `Analiza este audio: "${file.name}". Genera el arreglo musical completo con notas_musicxml para cada instrumento.`
        }]
      }]
    })
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error?.message || 'Error en la API de Claude');
  }

  const data = await response.json();
  let raw = data.content[0].text.trim();
  if (raw.startsWith('```')) {
    raw = raw.split('```')[1];
    if (raw.startsWith('json')) raw = raw.slice(4);
  }
  return JSON.parse(raw.trim());
}

// ── Generar MusicXML ────────────────────────────────
function generateMusicXML(analysis) {
  const tempo = analysis.tempo || 120;
  const [tsNum, tsDen] = (analysis.compas || '4/4').split('/').map(Number);
  const title = analysis.titulo || 'Transcript IA';
  const key = analysis.tonalidad || 'C major';
  const divisions = 4;

  const PITCH_TABLE = {
    0:['C',0],1:['C',1],2:['D',0],3:['D',1],4:['E',0],5:['F',0],
    6:['F',1],7:['G',0],8:['G',1],9:['A',0],10:['A',1],11:['B',0]
  };

  const KEY_FIFTHS = {
    'C major':0,'G major':1,'D major':2,'A major':3,'E major':4,'B major':5,
    'F major':-1,'Bb major':-2,'Eb major':-3,'Ab major':-4,
    'A minor':0,'E minor':1,'B minor':2,'D minor':-1,'G minor':-2,'C minor':-3
  };

  const DURATION_MAP = [
    [4.0,'whole',0],[3.0,'half',1],[2.0,'half',0],[1.5,'quarter',1],
    [1.0,'quarter',0],[0.75,'eighth',1],[0.5,'eighth',0],[0.25,'16th',0]
  ];

  function durToType(beats) {
    for (const [th, type, dots] of DURATION_MAP) {
      if (beats >= th * 0.9) return [type, dots];
    }
    return ['16th', 0];
  }

  const instrumentos = analysis.instrumentos || [];
  let partList = '';
  let parts = '';

  instrumentos.forEach((inst, i) => {
    const pid = `P${i+1}`;
    partList += `<score-part id="${pid}"><part-name>${inst.nombre}</part-name>
      <score-instrument id="${pid}-I1"><instrument-name>${inst.nombre}</instrument-name></score-instrument>
      <midi-instrument id="${pid}-I1"><midi-channel>${i+1}</midi-channel>
      <midi-program>${(inst.midi_program||0)+1}</midi-program></midi-instrument></score-part>\n`;

    // Recopilar todas las notas
    let allNotes = [];
    (inst.secciones || []).forEach(sec => {
      (sec.notas_musicxml || []).forEach(n => allNotes.push(n));
    });

    if (!allNotes.length) {
      // Notas por defecto si Claude no las dio
      allNotes = [{pitch:60,duracion:1,compas:1},{pitch:62,duracion:1,compas:1},
                  {pitch:64,duracion:1,compas:1},{pitch:65,duracion:1,compas:1}];
    }

    // Agrupar por compás
    const byMeasure = {};
    allNotes.forEach(n => {
      const m = n.compas || 1;
      if (!byMeasure[m]) byMeasure[m] = [];
      byMeasure[m].push(n);
    });

    const maxMeasure = Math.max(...Object.keys(byMeasure).map(Number), 8);
    const fifths = KEY_FIFTHS[key] !== undefined ? KEY_FIFTHS[key] : 0;
    const mode = key.includes('minor') ? 'minor' : 'major';
    const clef = inst.nombre === 'Bass' ? '<clef><sign>F</sign><line>4</line></clef>' : '<clef><sign>G</sign><line>2</line></clef>';

    let measuresXML = '';
    for (let m = 1; m <= maxMeasure; m++) {
      const notes = byMeasure[m] || [];
      let notesXML = '';
      let usedBeats = 0;

      notes.forEach(n => {
        const pitch = n.pitch;
        const dur = Math.max(0.25, Math.min(n.duracion || 1, tsNum));
        const durDiv = Math.round(dur * divisions);
        const [step, alter] = PITCH_TABLE[pitch % 12] || ['C', 0];
        const octave = Math.floor(pitch / 12) - 1;
        const [type, dots] = durToType(dur);

        notesXML += `<note>
          <pitch><step>${step}</step>${alter ? `<alter>${alter}</alter>` : ''}<octave>${octave}</octave></pitch>
          <duration>${durDiv}</duration><voice>1</voice><type>${type}</type>${dots ? '<dot/>' : ''}
        </note>`;
        usedBeats += dur;
      });

      // Rellenar compás con silencio si falta
      const remaining = tsNum - usedBeats;
      if (remaining > 0.1) {
        const [type] = durToType(remaining);
        notesXML += `<note><rest/><duration>${Math.round(remaining*divisions)}</duration><voice>1</voice><type>${type}</type></note>`;
      }

      const attrs = m === 1 ? `<attributes>
        <divisions>${divisions}</divisions>
        <key><fifths>${fifths}</fifths><mode>${mode}</mode></key>
        <time><beats>${tsNum}</beats><beat-type>${tsDen}</beat-type></time>
        ${clef}
      </attributes>
      <direction placement="above"><direction-type><metronome parentheses="no">
        <beat-unit>quarter</beat-unit><per-minute>${tempo}</per-minute>
      </metronome></direction-type><sound tempo="${tempo}"/></direction>` : '';

      measuresXML += `<measure number="${m}">${attrs}${notesXML}</measure>\n`;
    }

    parts += `<part id="${pid}">${measuresXML}</part>\n`;
  });

  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <work><work-title>${title}</work-title></work>
  <identification><encoding>
    <software>Transcript IA — Powered by Claude AI</software>
    <encoding-date>${new Date().toISOString().split('T')[0]}</encoding-date>
  </encoding></identification>
  <part-list>${partList}</part-list>
  ${parts}
</score-partwise>`;
}

// ── Generar PDF simple ──────────────────────────────
function generatePDF(analysis) {
  const win = window.open('', '_blank');
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
  <title>${analysis.titulo || 'Arreglo'}</title>
  <style>
    body{font-family:'Courier New',monospace;background:#060608;color:#edeae0;padding:40px;max-width:800px;margin:0 auto;}
    h1{color:#00ff87;font-size:32px;border-bottom:2px solid #00ff87;padding-bottom:12px;}
    h2{color:#e8c547;font-size:16px;margin-top:32px;letter-spacing:3px;text-transform:uppercase;}
    h3{color:#00ff87;font-size:13px;margin-top:20px;}
    .info{display:flex;gap:24px;flex-wrap:wrap;margin:20px 0;padding:16px;background:#0f0f14;border:1px solid #1c1c24;}
    .info-item{text-align:center;} .info-label{font-size:9px;color:#48485a;letter-spacing:2px;text-transform:uppercase;}
    .info-val{font-size:18px;color:#00ff87;font-weight:bold;}
    .sec-table{width:100%;border-collapse:collapse;margin:12px 0;}
    .sec-table th{background:#0f0f14;color:#00ff87;padding:8px;text-align:left;font-size:11px;letter-spacing:2px;}
    .sec-table td{padding:8px;border-bottom:1px solid #1c1c24;font-size:12px;}
    .sec-table tr:nth-child(even) td{background:#0a0a0e;}
    .inst-block{background:#0f0f14;border:1px solid #1c1c24;padding:16px;margin:12px 0;}
    .tag{display:inline-block;background:#00ff87;color:#000;font-size:10px;padding:2px 8px;margin:2px;font-weight:bold;}
    .footer{margin-top:40px;padding-top:16px;border-top:1px solid #1c1c24;font-size:10px;color:#48485a;text-align:center;}
    @media print{body{background:#fff;color:#000;} h1,h2,h3{color:#000;} .info{background:#f5f5f5;} .inst-block{background:#f9f9f9;} .tag{background:#000;color:#fff;}}
  </style></head><body>
  <h1>🎵 ${analysis.titulo || 'Arreglo Musical'}</h1>
  <div class="info">
    <div class="info-item"><div class="info-label">Tonalidad</div><div class="info-val">${analysis.tonalidad||'–'}</div></div>
    <div class="info-item"><div class="info-label">Tempo</div><div class="info-val">${analysis.tempo||'–'} BPM</div></div>
    <div class="info-item"><div class="info-label">Compás</div><div class="info-val">${analysis.compas||'4/4'}</div></div>
    <div class="info-item"><div class="info-label">Género</div><div class="info-val">${analysis.genero||'–'}</div></div>
    <div class="info-item"><div class="info-label">Duración</div><div class="info-val">${analysis.duracion_total||'–'}</div></div>
  </div>
  <h2>▸ Estructura</h2>
  <table class="sec-table"><tr><th>Sección</th><th>Compases</th><th>Descripción</th></tr>
  ${(analysis.estructura||[]).map(s=>`<tr><td><b>${s.seccion}</b></td><td>${s.compases}</td><td>${s.descripcion}</td></tr>`).join('')}
  </table>
  <h2>▸ Arreglo por Instrumento</h2>
  ${(analysis.instrumentos||[]).map(inst=>`
    <div class="inst-block">
      <h3>◈ ${inst.nombre.toUpperCase()} — Rango: ${inst.rango||'–'} · MIDI: ${inst.midi_program||0}</h3>
      ${(inst.secciones||[]).map(sec=>`
        <p><b style="color:#e8c547">${sec.nombre}:</b> ${sec.descripcion}</p>
        ${sec.patron?`<p style="color:#00ff87;font-size:11px">Patrón: ${sec.patron}</p>`:''}
        ${(sec.tecnicas||[]).map(t=>`<span class="tag">${t}</span>`).join('')}
      `).join('')}
    </div>`).join('')}
  <h2>▸ Armonía</h2>
  <p><b>Progresión principal:</b> <span style="color:#00ff87">${analysis.armonia?.progresion_principal||'–'}</span></p>
  <p><b>Modo:</b> ${analysis.armonia?.modo||'–'}</p>
  <h2>▸ Notas del Arreglista</h2>
  <p>${analysis.notas_arreglista||'–'}</p>
  <div class="footer">Generado por Transcript IA · Powered by Claude AI · ${new Date().toLocaleDateString()}</div>
  <script>window.onload=()=>{window.print();}<\/script>
  </body></html>`;
  win.document.write(html);
  win.document.close();
}

// ── Generar Markdown ────────────────────────────────
function generateMarkdown(analysis) {
  let md = `# 🎵 ${analysis.titulo || 'Arreglo Musical'}\n\n`;
  md += `**Tonalidad:** ${analysis.tonalidad} | **Tempo:** ${analysis.tempo} BPM | **Compás:** ${analysis.compas} | **Género:** ${analysis.genero}\n\n`;
  md += `## Estructura\n\n| Sección | Compases | Descripción |\n|---------|----------|-------------|\n`;
  (analysis.estructura||[]).forEach(s => { md += `| ${s.seccion} | ${s.compases} | ${s.descripcion} |\n`; });
  md += `\n## Instrumentos\n\n`;
  (analysis.instrumentos||[]).forEach(inst => {
    md += `### ${inst.nombre}\n`;
    (inst.secciones||[]).forEach(sec => {
      md += `**${sec.nombre}:** ${sec.descripcion}\n`;
      if (sec.patron) md += `- Patrón: \`${sec.patron}\`\n`;
      if (sec.tecnicas?.length) md += `- Técnicas: ${sec.tecnicas.join(', ')}\n`;
    });
    md += '\n';
  });
  md += `## Armonía\n\n**Progresión:** ${analysis.armonia?.progresion_principal}\n\n`;
  md += `## Notas del Arreglista\n\n${analysis.notas_arreglista}\n\n---\n*Generado por Transcript IA · Powered by Claude AI*\n`;
  return md;
}

// ── Mostrar resultado ───────────────────────────────
function showResult(analysis) {
  // Scroll a sección de exportar
  document.querySelector('.export-section')?.scrollIntoView({behavior:'smooth'});

  // Mostrar banner de éxito
  let banner = document.getElementById('analysisBanner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'analysisBanner';
    banner.style.cssText = `
      position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
      background:#0f0f14;border:1px solid #00ff87;
      padding:16px 32px;z-index:9997;
      font-family:'IBM Plex Mono',monospace;font-size:12px;
      color:#00ff87;letter-spacing:2px;text-align:center;
      box-shadow:0 0 30px rgba(0,255,135,.3);
    `;
    document.body.appendChild(banner);
  }
  banner.innerHTML = `✅ ANÁLISIS COMPLETO — ${analysis.titulo} · ${analysis.tonalidad} · ${analysis.tempo} BPM`;
  setTimeout(() => banner.remove(), 6000);
}

// ── handleFile principal ────────────────────────────
function handleFile(f) {
  if (!f) return;
  currentFile = f;

  // Guardar en historial
  const h = getHist();
  h.unshift({
    name: f.name, size: f.size,
    date: new Date().toLocaleDateString('es-CO',{day:'2-digit',month:'short',year:'numeric'}),
    id: Date.now()
  });
  if (h.length > 10) h.pop();
  localStorage.setItem('tia_h', JSON.stringify(h));
  renderHistory();

  // Verificar API key
  if (!apiKey) {
    showApiKeyModal(() => runAnalysis(f));
  } else {
    runAnalysis(f);
  }
}

async function runAnalysis(f) {
  try {
    const analysis = await analyzeWithClaude(f);
    currentAnalysis = analysis;
    hideProgress();
    showResult(analysis);
  } catch(e) {
    hideProgress();
    if (e.message?.includes('401') || e.message?.includes('auth')) {
      apiKey = '';
      localStorage.removeItem('tia_apikey');
      alert('API key inválida. Por favor verifica tu clave.');
      showApiKeyModal(() => runAnalysis(f));
    } else {
      alert('Error al analizar: ' + e.message);
    }
  }
}

// ── Botones de exportar ─────────────────────────────
function exportPDF() {
  if (!currentAnalysis) { alert('Primero sube y analiza una canción.'); return; }
  generatePDF(currentAnalysis);
}

function exportMusicXML() {
  if (!currentAnalysis) { alert('Primero sube y analiza una canción.'); return; }
  const xml = generateMusicXML(currentAnalysis);
  const blob = new Blob([xml], {type:'application/xml'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (currentAnalysis.titulo || 'arreglo').replace(/[^a-zA-Z0-9]/g,'_') + '.musicxml';
  a.click();
}

function exportMarkdown() {
  if (!currentAnalysis) { alert('Primero sube y analiza una canción.'); return; }
  const md = generateMarkdown(currentAnalysis);
  const blob = new Blob([md], {type:'text/markdown'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (currentAnalysis.titulo || 'arreglo').replace(/[^a-zA-Z0-9]/g,'_') + '.md';
  a.click();
}

function shareLink() {
  if (!currentAnalysis) { alert('Primero sube y analiza una canción.'); return; }
  const data = btoa(encodeURIComponent(JSON.stringify(currentAnalysis)));
  const url = window.location.href.split('?')[0] + '?a=' + data;
  navigator.clipboard.writeText(url).then(() => {
    alert('✅ Link copiado al portapapeles');
  });
}

// Cargar análisis compartido desde URL
window.addEventListener('load', () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('a')) {
    try {
      currentAnalysis = JSON.parse(decodeURIComponent(atob(params.get('a'))));
      showResult(currentAnalysis);
    } catch(e) {}
  }
});

// CSS para spinner
const style = document.createElement('style');
style.textContent = '@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}';
document.head.appendChild(style);
