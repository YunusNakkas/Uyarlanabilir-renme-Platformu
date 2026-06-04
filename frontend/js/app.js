    const API_BASE =
        window.location.protocol === "file:" || (window.location.hostname === "127.0.0.1" && window.location.port !== "8000")
            ? "http://127.0.0.1:8000"
            : "";

    // ── AUTH ──────────────────────────────────────────────
    // Token sadece bellekte tutulur — sayfa yenilenince sıfırlanır, login'e yönlendirir
    localStorage.removeItem("eduai_token"); // eski oturumdan kalma temizle
    let _memToken = sessionStorage.getItem("_eduai_t") || null;
    if (_memToken) sessionStorage.removeItem("_eduai_t"); // bir kez okunur, hemen silinir

    function getToken() { return _memToken; }
    function clearToken() { _memToken = null; }

    function authHeaders() {
        return _memToken ? { "Authorization": `Bearer ${_memToken}` } : {};
    }

    function updateSidebarUser(data) {
        const fullName = [data.ad, data.soyad].filter(Boolean).join(" ");
        const display = fullName || data.email || "--";
        const initials = fullName
            ? (data.ad[0] + (data.soyad ? data.soyad[0] : "")).toUpperCase()
            : (data.email || "?").slice(0, 2).toUpperCase();
        document.getElementById("userAvatar").innerText = initials;
        document.getElementById("userDisplayName").innerText = display;
    }

    function hideSplash() {
        const s = document.getElementById("loadingScreen");
        if (s) s.style.display = "none";
    }

    async function checkAuth() {
        const token = getToken();
        if (!token) { window.location.replace("/login"); return; }
        try {
            const controller = new AbortController();
            const tid = setTimeout(() => controller.abort(), 5000);
            const res = await fetch(`${API_BASE}/auth/me`, {
                headers: { "Authorization": `Bearer ${token}` },
                signal: controller.signal
            });
            clearTimeout(tid);
            if (!res.ok) { clearToken(); window.location.replace("/login"); return; }
            const data = await res.json();
            updateSidebarUser(data);
            document.getElementById("appShell").style.display = "flex";
            hideSplash();
        } catch (err) {
            console.error("Auth hatası:", err);
            clearToken();
            window.location.replace("/login");
        }
    }

    document.getElementById("logoutBtn").addEventListener("click", () => {
        clearToken();
        window.location.replace("/login");
    });

    checkAuth();
    // ── AUTH SON ──────────────────────────────────────────

    // Modalı kapatma işlemleri
    const modal = document.getElementById('aiModal');
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalDot = document.getElementById('modal-dot');

    modalClose.addEventListener('click', () => modal.classList.remove('show'));
    modal.addEventListener('click', (e) => { if(e.target === modal) modal.classList.remove('show'); });

    // Sol menüde derse tıklanınca Popup açılsın ve ilgili kart görünür alana kaysın
    const navToDataMap = {
        'nav-matematik': { base: 'mat', color: '#0F6E56', dotColor: '#1D9E75', lessonId: 'ders-matematik' },
        'nav-fizik': { base: 'fiz', color: '#A32D2D', dotColor: '#E24B4A', lessonId: 'ders-fizik' },
        'nav-kimya': { base: 'kim', color: '#854F0B', dotColor: '#BA7517', lessonId: 'ders-kimya' },
        'nav-uyku': { base: 'uyku', color: '#6D28D9', dotColor: '#8B5CF6', lessonId: 'ders-uyku' },
        'nav-calisma': { base: 'calisma', color: '#B45309', dotColor: '#F59E0B', lessonId: 'ders-calisma' }
    };

    Object.keys(navToDataMap).forEach(navId => {
        const navItem = document.getElementById(navId);
        if(!navItem) return;
        
        navItem.style.cursor = 'pointer';
        navItem.addEventListener('click', () => {
            const data = navToDataMap[navId];
            
            // Arkadaki kartı hala hizala ki deneyim bozulmasın
            const lessonCard = document.getElementById(data.lessonId);
            if(lessonCard) lessonCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Popup için verileri çekip göster
            const baslikElement = document.getElementById(`ui-${data.base}-baslik`);
            const bodyElement = document.getElementById(`ui-${data.base}-tavsiyeler`);
            
            if(baslikElement && bodyElement) {
                 modalTitle.innerText = baslikElement.innerText || baslikElement.textContent;
                 modalTitle.style.color = data.color;
                 modalDot.style.backgroundColor = data.dotColor;
                 modalBody.innerHTML = bodyElement.innerHTML;
                 
                 modal.classList.add('show');
            }
        });
    });

    // Önceki analiz değerlerini saklamak ve fark hesaplamak için basit depolama
    const trendStorageKey = 'eduai_prev_ders_performans';

    function getPreviousPerformance() {
        try {
            const raw = localStorage.getItem(trendStorageKey);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            console.warn('Önceki performans okunamadı:', e);
            return null;
        }
    }

    function setPreviousPerformance(obj) {
        try {
            localStorage.setItem(trendStorageKey, JSON.stringify(obj));
        } catch (e) {
            console.warn('Önceki performans kaydedilemedi:', e);
        }
    }

    function formatTrend(current, previous) {
        if (previous === null || previous === undefined) {
            return '—';
        }
        const diff = current - previous;
        if (diff > 0) {
            return `+${diff} ↑`;
        } else if (diff < 0) {
            return `${diff} ↓`;
        }
        return '0 →';
    }

    // Fark analizi kartı: notlardan gelen seviye ile alışkanlıktan tahmin edilen seviyeyi kıyaslar.
    function renderGapCard(gap) {
        const el = document.getElementById('ui-gap-card');
        if (!el) return;
        if (!gap) { el.style.display = 'none'; return; }
        // Duruma göre renk (risk: turuncu, potansiyel: mavi, düşük: kırmızı, tutarlı: yeşil)
        const palette = {
            '⚠️': { bg: 'var(--acc-gold-bg)',   border: 'var(--acc-gold-bd)',   text: 'var(--acc-gold-fg)',   fill: '#E8923C' },
            '💡': { bg: 'var(--acc-blue-bg)',   border: 'var(--acc-blue-bd)',   text: 'var(--acc-blue-fg)',   fill: '#378ADD' },
            '🔴': { bg: 'var(--acc-red-bg)',    border: 'var(--acc-red-bd)',    text: 'var(--acc-red-fg)',    fill: '#D94F4F' },
            '✅': { bg: 'var(--acc-green-bg)',  border: 'var(--acc-green-bd)',  text: 'var(--acc-green-fg)',  fill: '#1D9E75' },
        };
        const c = palette[gap.icon] || palette['✅'];
        const pill = (label, val) =>
            `<span style="font-size:11px;color:var(--color-text-tertiary);">${label}</span> ` +
            `<span style="font-size:12px;font-weight:700;color:${c.text};background:var(--color-background-primary);border:1px solid ${c.border};border-radius:6px;padding:2px 8px;">${val}</span>`;

        el.style.display = 'block';
        el.innerHTML = `
            <div style="background:${c.bg};border:1px solid ${c.border};border-radius:12px;padding:16px;margin-bottom:16px;">
              <div style="display:flex;align-items:center;gap:9px;margin-bottom:10px;">
                <span style="font-size:20px;">${gap.icon}</span>
                <span style="font-size:14.5px;font-weight:700;color:${c.text};">${gap.headline}</span>
              </div>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:11px;">
                ${pill('Notların', gap.grade_tier_name)}
                <span style="color:${c.text};font-weight:700;">→</span>
                ${pill('Alışkanlıkların', gap.habit_tier_name)}
              </div>
              <div style="font-size:12.5px;line-height:1.65;color:var(--color-text-primary);margin-bottom:10px;">${gap.message}</div>
              <div style="display:flex;align-items:flex-start;gap:7px;background:var(--color-background-primary);border:1px dashed ${c.border};border-radius:8px;padding:9px 11px;font-size:12px;line-height:1.55;color:var(--color-text-primary);">
                <span style="flex-shrink:0;">🎯</span>
                <span><b>Sonraki adım:</b> ${gap.next_step}</span>
              </div>
            </div>`;
    }

    const navIlerleme = document.getElementById('nav-ilerleme');
    if (navIlerleme) {
        navIlerleme.addEventListener('click', async () => {
            modalTitle.innerText = "İlerleme Raporu";
            modalTitle.style.color = '#185FA5';
            modalDot.style.backgroundColor = '#378ADD';
            modalBody.innerHTML = `<div style="text-align:center;padding:30px;color:var(--color-text-tertiary);">Yükleniyor...</div>`;
            modal.classList.add('show');

            try {
                const res = await fetch(`${API_BASE}/api/analytics`, { headers: authHeaders() });
                if (!res.ok) throw new Error();
                const data = await res.json();
                const analyses = data.analyses || [];

                if (!analyses.length) {
                    modalBody.innerHTML = `
                        <div style="text-align:center;padding:40px 20px;color:var(--color-text-tertiary);">
                            <div style="font-size:32px;margin-bottom:12px;">📊</div>
                            <div style="font-size:14px;">Henüz analiz yapılmamış.<br>İlk analizini yaptıktan sonra burada görünecek.</div>
                        </div>`;
                    return;
                }

                const last  = analyses[analyses.length - 1];
                const first = analyses[0];
                const trend = analyses.length > 1 ? last.genel - first.genel : null;
                const trendColor = trend >= 0 ? '#1D9E75' : '#d94f4f';

                const dersler = [
                    { isim: 'Matematik', deger: last.mat, renk: '#1D9E75' },
                    { isim: 'Fizik',     deger: last.fiz, renk: '#378ADD' },
                    { isim: 'Kimya',     deger: last.kim, renk: '#D85A30' },
                ];
                const guclu = [...dersler].sort((a,b) => b.deger - a.deger)[0];
                const zayif = [...dersler].sort((a,b) => a.deger - b.deger)[0];

                modalBody.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">
                        <div style="background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                            <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">Genel Ortalama</div>
                            <div style="font-size:24px;font-weight:700;color:#1D9E75;">${last.genel}</div>
                            <div style="font-size:10px;color:var(--color-text-tertiary);">Son analiz</div>
                        </div>
                        <div style="background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                            <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">En Güçlü</div>
                            <div style="font-size:18px;font-weight:700;color:#0F6E56;">${guclu.isim}</div>
                            <div style="font-size:10px;color:var(--color-text-tertiary);">Ort. ${guclu.deger}/100</div>
                        </div>
                        <div style="background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                            <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">Gelişmeli</div>
                            <div style="font-size:18px;font-weight:700;color:#185FA5;">${zayif.isim}</div>
                            <div style="font-size:10px;color:var(--color-text-tertiary);">Ort. ${zayif.deger}/100</div>
                        </div>
                    </div>

                    <div style="background:var(--color-background-primary);border:1px solid rgba(0,0,0,0.08);border-radius:12px;padding:16px;margin-bottom:12px;">
                        <div style="font-size:13px;font-weight:600;color:var(--color-text-primary);margin-bottom:14px;">Son Analiz Performansı
                            <span style="font-size:11px;font-weight:400;color:var(--color-text-tertiary);margin-left:6px;">${last.tarih}</span>
                        </div>
                        ${dersler.map(d => `
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                            <div style="font-size:12px;color:var(--color-text-secondary);min-width:68px;">${d.isim}</div>
                            <div style="flex:1;background:#f0f0ee;border-radius:20px;height:7px;">
                                <div style="width:${d.deger}%;background:${d.renk};height:7px;border-radius:20px;transition:width 0.5s;"></div>
                            </div>
                            <div style="font-size:12px;font-weight:600;color:${d.renk};min-width:28px;text-align:right;">${d.deger}</div>
                        </div>`).join('')}
                        ${trend !== null ? `
                        <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(0,0,0,0.06);font-size:12px;color:var(--color-text-secondary);">
                            İlk analizden bu yana: <span style="color:${trendColor};font-weight:700;">${trend >= 0 ? '+' : ''}${trend} puan</span>
                            <span style="color:var(--color-text-tertiary);"> (${analyses.length} analiz)</span>
                        </div>` : ''}
                    </div>
                `;
            } catch {
                modalBody.innerHTML = `<div style="color:#d94f4f;padding:20px;text-align:center;">Veriler yüklenemedi.</div>`;
            }
        });
    }

    // Kutucuklardaki sayılar değiştikçe renkleri güncelleyen fonksiyon
    document.querySelectorAll('.grow').forEach(row => {
        const input = row.querySelector('.ginput');
        const scoreBox = row.querySelector('.gscore');
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') e.preventDefault();
        });
        input.addEventListener('input', (e) => {
            let val = parseInt(e.target.value) || 0;
            if (input.id === 'uyku-saati' || input.id === 'calisma-saati') {
                 if (val > 24) val = 24; if(val < 0) val = 0;
                 scoreBox.innerText = val;
                 if (input.id === 'uyku-saati') {
                     scoreBox.className = 'gscore ' + (val < 6 ? 'sl' : (val <= 8 ? 'sh' : 'sm'));
                 } else {
                     scoreBox.className = 'gscore ' + (val < 2 ? 'sl' : (val < 4 ? 'sm' : 'sh'));
                 }
            } else {
                if(val > 100) val = 100; if(val < 0) val = 0;
                scoreBox.innerText = val;
                scoreBox.className = 'gscore ' + (val < 60 ? 'sl' : (val < 80 ? 'sm' : 'sh'));
            }
        });
    });

    document.getElementById('analizBtn').addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        const btn = document.getElementById('analizBtn');
        const alan = document.getElementById('ai-sonuc-alani');
        
        try {
            const notlar = {
                mat: [Number(document.getElementById('mat1').value), Number(document.getElementById('mat2').value), Number(document.getElementById('mat3').value)],
                fiz: [Number(document.getElementById('fiz1').value), Number(document.getElementById('fiz2').value), Number(document.getElementById('fiz3').value)],
                kim: [Number(document.getElementById('kim1').value), Number(document.getElementById('kim2').value), Number(document.getElementById('kim3').value)]
            };

            const allGrades = [...notlar.mat, ...notlar.fiz, ...notlar.kim];
            const areAllSame = allGrades.every(val => val === allGrades[0]);
            const hasZero = allGrades.includes(0);

            if (areAllSame || hasZero) {
                alert("Tüm notlar aynı olamaz veya '0' not girilemez. Lütfen bir kez daha girin.");
                return;
            }

            const rutinler = {
                uyku: Number(document.getElementById('uyku-saati').value),
                calisma: Number(document.getElementById('calisma-saati').value)
            };

            const ortalamalar = {
                mat: Math.round((notlar.mat[0] + notlar.mat[1] + notlar.mat[2]) / 3),
                fiz: Math.round((notlar.fiz[0] + notlar.fiz[1] + notlar.fiz[2]) / 3),
                kim: Math.round((notlar.kim[0] + notlar.kim[1] + notlar.kim[2]) / 3)
            };

            btn.disabled = true;
            btn.innerText = "Sunucuya bağlanılıyor...";
            alan.style.opacity = "0.4";

            btn.innerText = "Analiz Ediliyor...";

            const _ctrl = new AbortController();
            const _tid = setTimeout(() => _ctrl.abort(), 90000);
            let response;
            try {
                response = await fetch(`${API_BASE}/api/analyze`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", ...authHeaders() },
                    body: JSON.stringify({ notlar, rutinler }),
                    signal: _ctrl.signal
                });
            } finally {
                clearTimeout(_tid);
            }

            if (!response.ok) {
                let msg = `Sunucu hatası (${response.status})`;
                try {
                    const errData = await response.json();
                    if (typeof errData.detail === "string") {
                        msg = errData.detail;
                    } else if (Array.isArray(errData.detail)) {
                        msg = errData.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
                    }
                } catch (_) { /* ignore */ }
                throw new Error(msg);
            }

            const payload = await response.json();
            const aiSonuc = payload.ai;
            if (!aiSonuc || typeof aiSonuc !== "object") {
                throw new Error("Sunucudan geçersiz yanıt alındı.");
            }

            const genelOrt = Math.round((ortalamalar.mat + ortalamalar.fiz + ortalamalar.kim) / 3);

            renderGapCard(payload.gap);

            const derslerArr = [
                {isim: 'Matematik', ort: ortalamalar.mat, id: 'mat', color: '#1D9E75'},
                {isim: 'Fizik', ort: ortalamalar.fiz, id: 'fiz', color: '#378ADD'},
                {isim: 'Kimya', ort: ortalamalar.kim, id: 'kim', color: '#D85A30'}
            ];

            const onceki = getPreviousPerformance() || { mat: null, fiz: null, kim: null, uyku: null, calisma: null };
            const trMat = formatTrend(ortalamalar.mat, onceki.mat);
            const trFiz = formatTrend(ortalamalar.fiz, onceki.fiz);
            const trKim = formatTrend(ortalamalar.kim, onceki.kim);
            const trUyku = formatTrend(rutinler.uyku, onceki.uyku);
            const trCalisma = formatTrend(rutinler.calisma, onceki.calisma);
            derslerArr.sort((a, b) => b.ort - a.ort);
            
            // En güçlü / gelişmeli derse en yüksek ve en düşük ortalamalı dersler
            // (kutular kaldırıldı; değişkenler aşağıda kaydetme/özet için hâlâ kullanılıyor)
            const guclu = derslerArr[0];
            const zayif = derslerArr[2];

            ['mat', 'fiz', 'kim'].forEach(ders => {
                document.getElementById(`ui-${ders}-score`).innerText = ortalamalar[ders];
                document.getElementById(`ui-${ders}-bar`).style.width = ortalamalar[ders] + '%';
            });
            const uykuPercent = Math.max(0, Math.min(100, Math.round((rutinler.uyku / 24) * 100)));
            const calismaPercent = Math.max(0, Math.min(100, Math.round((rutinler.calisma / 24) * 100)));

            document.getElementById('ui-uyku-score').innerText = rutinler.uyku;
            document.getElementById('ui-uyku-bar').style.width = uykuPercent + '%';
            document.getElementById('ui-uyku-trend').innerText = trUyku;

            document.getElementById('ui-calisma-score').innerText = rutinler.calisma;
            document.getElementById('ui-calisma-bar').style.width = calismaPercent + '%';
            document.getElementById('ui-calisma-trend').innerText = trCalisma;

            // Önceki analiz değerlerine göre trendleri güncelle
            document.getElementById('ui-mat-trend').innerText = trMat;
            document.getElementById('ui-fiz-trend').innerText = trFiz;
            document.getElementById('ui-kim-trend').innerText = trKim;

            // React island'a (Akademik Özet) veriyi gönder
            window.dispatchEvent(new CustomEvent('eduai:analiz', { detail: {
                genelOrt,
                guclu: { isim: guclu.isim, ort: guclu.ort, color: guclu.color },
                zayif: { isim: zayif.isim, ort: zayif.ort, color: zayif.color },
                ortalamalar,
                rutinler
            }}));

            // GÜNCELLENEN KISIM: Ders isimleri sabit, AI yanıtı temizlenerek ekleniyor.
            // AI bazen "Matematik - Güçlü" diyebilir, replace ile baştaki tekrarı engelliyoruz.
            let matOzet = (aiSonuc.matematikDurum || aiSonuc.matematikBaslik || "").replace(/Matematik\s*[-—:]\s*/i, '');
            document.getElementById('ui-mat-baslik').innerText = `Matematik — ${matOzet}`;
            document.getElementById('ui-mat-tavsiyeler').innerHTML = aiSonuc.matematikTavsiyeler.map(t => 
                `<div class="aitem"><div class="adot" style="background:#1D9E75;"></div><div class="atext">${t}</div></div>`
            ).join('');

            let fizOzet = (aiSonuc.fizikDurum || aiSonuc.fizikBaslik || "").replace(/Fizik\s*[-—:]\s*/i, '');
            document.getElementById('ui-fiz-baslik').innerText = `Fizik — ${fizOzet}`;
            document.getElementById('ui-fiz-tavsiyeler').innerHTML = aiSonuc.fizikTavsiyeler.map(t => 
                `<div class="aitem"><div class="adot" style="background:#E24B4A;"></div><div class="atext">${t}</div></div>`
            ).join('');

            let kimOzet = (aiSonuc.kimyaDurum || aiSonuc.kimyaBaslik || "").replace(/Kimya\s*[-—:]\s*/i, '');
            document.getElementById('ui-kim-baslik').innerText = `Kimya — ${kimOzet}`;
            document.getElementById('ui-kim-tavsiyeler').innerHTML = aiSonuc.kimyaTavsiyeler.map(t => 
                `<div class="aitem"><div class="adot" style="background:#BA7517;"></div><div class="atext">${t}</div></div>`
            ).join('');

            let uykuOzet = (aiSonuc.uykuDurum || aiSonuc.uykuBaslik || "");
            document.getElementById('ui-uyku-baslik').innerText = `Uyku Düzeni — ${uykuOzet}`;
            document.getElementById('ui-uyku-tavsiyeler').innerHTML = (aiSonuc.uykuTavsiyeler || []).map(t => 
                `<div class="aitem"><div class="adot" style="background:#8B5CF6;"></div><div class="atext">${t}</div></div>`
            ).join('');

            let calismaOzet = (aiSonuc.calismaDurum || aiSonuc.calismaBaslik || "");
            document.getElementById('ui-calisma-baslik').innerText = `Ders Çalışma Saati — ${calismaOzet}`;
            document.getElementById('ui-calisma-tavsiyeler').innerHTML = (aiSonuc.calismaTavsiyeler || []).map(t => 
                `<div class="aitem"><div class="adot" style="background:#F59E0B;"></div><div class="atext">${t}</div></div>`
            ).join('');

            setPreviousPerformance({
                mat: ortalamalar.mat,
                fiz: ortalamalar.fiz,
                kim: ortalamalar.kim,
                uyku: rutinler.uyku,
                calisma: rutinler.calisma
            });

            alan.style.opacity = "1";
            alan.style.pointerEvents = "auto";
            document.getElementById('pdfBtn').style.display = "block";
            document.getElementById('pathBtn').style.display = "block";
            document.getElementById('mailBtn').style.display = "block";
            window._lastInput = { notlar, rutinler };
            // Mail butonu için son rapor verisini sakla
            window._lastReport = {
                genel_ort: genelOrt,
                guclu: guclu.isim,
                zayif: zayif.isim,
                ai: aiSonuc
            };

        } catch (error) {
            const msg = error.name === "AbortError"
                ? "Sunucu 90 saniyede yanıt vermedi. Lütfen tekrar deneyin."
                : "İşlem sırasında bir hata oluştu:\n" + error.message;
            alert(msg);
        } finally {
            btn.disabled = false;
            btn.innerText = "Tekrar Analiz Et";
        }
    });

    document.getElementById('mailBtn').addEventListener('click', async () => {
        const btn = document.getElementById('mailBtn');
        if (!window._lastReport) { alert("Önce analiz yapın."); return; }
        const original = btn.innerText;
        btn.disabled = true;
        btn.innerText = "Gönderiliyor...";
        try {
            const res = await fetch(`${API_BASE}/api/send-report`, {
                method: "POST",
                headers: { "Content-Type": "application/json", ...authHeaders() },
                body: JSON.stringify(window._lastReport)
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.detail || "Mail gönderilemedi.");
            btn.innerText = "✓ Gönderildi";
            alert(`Rapor mailin ${data.to} adresine gönderildi.`);
        } catch (err) {
            btn.innerText = original;
            alert("Mail gönderilemedi:\n" + err.message);
        } finally {
            btn.disabled = false;
            setTimeout(() => { btn.innerText = original; }, 3000);
        }
    });

    document.getElementById('pathBtn').addEventListener('click', async () => {
        const btn = document.getElementById('pathBtn');
        if (!window._lastInput) {
            alert("Önce analiz yapmalısınız.");
            return;
        }
        btn.disabled = true;
        const original = btn.innerText;
        btn.innerText = "Hazırlanıyor...";
        try {
            const res = await fetch(`${API_BASE}/api/learning-path`, {
                method: "POST",
                headers: { "Content-Type": "application/json", ...authHeaders() },
                body: JSON.stringify(window._lastInput)
            });
            if (!res.ok) {
                let msg = `Sunucu hatası (${res.status})`;
                try { const e = await res.json(); if (typeof e.detail === "string") msg = e.detail; } catch {}
                throw new Error(msg);
            }
            const data = await res.json();
            renderLearningPath(data.plan);
        } catch (err) {
            alert("Öğrenme yolu oluşturulamadı:\n" + err.message);
        } finally {
            btn.disabled = false;
            btn.innerText = original;
        }
    });

    function renderLearningPath(plan) {
        if (!plan || !Array.isArray(plan.haftalar)) {
            alert("Geçersiz öğrenme yolu yanıtı.");
            return;
        }
        const colors = { matematik: "#1D9E75", fizik: "#378ADD", kimya: "#D85A30" };
        const haftalarHtml = plan.haftalar.map(h => {
            const gorevlerHtml = ["matematik","fizik","kimya"].map(ders => {
                const items = (h.gorevler && h.gorevler[ders]) || [];
                if (!items.length) return "";
                return `
                    <div style="margin-top:10px;">
                        <div style="font-size:12px;font-weight:600;color:${colors[ders]};text-transform:capitalize;margin-bottom:6px;">${ders}</div>
                        ${items.map(t => `<div class="aitem"><div class="adot" style="background:${colors[ders]};"></div><div class="atext">${t}</div></div>`).join("")}
                    </div>`;
            }).join("");
            return `
                <div style="border:1px solid rgba(0,0,0,0.1);border-radius:10px;padding:14px;margin-bottom:14px;background:var(--color-background-primary);">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <div style="width:28px;height:28px;border-radius:8px;background:#ede9fe;color:#6d28d9;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;">${h.hafta}</div>
                        <div style="flex:1;">
                            <div style="font-size:14px;font-weight:600;color:var(--color-text-primary);">Hafta ${h.hafta}</div>
                            <div style="font-size:12px;color:var(--color-text-secondary);">${h.odak || ""}</div>
                        </div>
                    </div>
                    ${gorevlerHtml}
                    ${h.motivasyon ? `<div style="margin-top:12px;padding:10px;background:var(--color-background-secondary);border-radius:8px;font-size:12px;color:var(--color-text-secondary);font-style:italic;">💡 ${h.motivasyon}</div>` : ""}
                </div>`;
        }).join("");

        modalTitle.innerText = "📚 Kişisel Öğrenme Yolun";
        modalTitle.style.color = "#6d28d9";
        modalDot.style.backgroundColor = "#8b5cf6";
        modalBody.innerHTML = `
            <div id="learningPathContent">
                ${plan.ozet ? `<div style="padding:12px;background:#f3e8ff;border:1px solid #d8b4fe;border-radius:10px;margin-bottom:14px;font-size:13px;color:#6d28d9;line-height:1.5;">${plan.ozet}</div>` : ""}
                ${plan.haftalikToplamSaat ? `<div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:14px;">Haftalık toplam çalışma: <b>${plan.haftalikToplamSaat} saat</b></div>` : ""}
                ${haftalarHtml}
            </div>
            <button id="learningPathPdfBtn" style="margin-top:8px;width:100%;background:#6d28d9;color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer;">📄 PDF İndir</button>
        `;
        modal.classList.add('show');

        const lpPdfBtn = document.getElementById('learningPathPdfBtn');
        lpPdfBtn.addEventListener('click', () => {
            const target = document.getElementById('learningPathContent');
            const opt = {
                margin:      0.4,
                filename:    'EduAI_Ogrenme_Yolum.pdf',
                image:       { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF:       { unit: 'in', format: 'a4', orientation: 'portrait' }
            };
            const original = lpPdfBtn.innerText;
            lpPdfBtn.disabled = true;
            lpPdfBtn.innerText = "İndiriliyor...";
            html2pdf().set(opt).from(target).save().then(() => {
                lpPdfBtn.disabled = false;
                lpPdfBtn.innerText = original;
            });
        });
    }

    document.getElementById('pdfBtn').addEventListener('click', () => {
        const btn = document.getElementById('pdfBtn');
        const alan = document.getElementById('ai-sonuc-alani');
        const opt = {
            margin:       0.4,
            filename:     'EduAI_Tavsiye_Raporum.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 },
            jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
        };
        btn.innerText = "İndiriliyor...";
        html2pdf().set(opt).from(alan).save().then(() => {
            btn.innerText = "📄 PDF İndir";
        });
    });

    // ── RAPORLAR ──────────────────────────────────────────
    let _analyticsChart = null;

    document.getElementById('nav-raporlar').addEventListener('click', async () => {
        modalTitle.innerText = "📊 Öğrenme Analitiği";
        modalTitle.style.color = "#E74C3C";
        modalDot.style.backgroundColor = "#E74C3C";
        modalBody.innerHTML = `<div style="text-align:center;padding:20px;color:var(--color-text-tertiary);">Yükleniyor...</div>`;
        modal.classList.add('show');

        try {
            const res = await fetch(`${API_BASE}/api/analytics`, { headers: authHeaders() });
            if (!res.ok) throw new Error("Veri alınamadı");
            const data = await res.json();
            renderAnalytics(data.analyses);
        } catch (err) {
            modalBody.innerHTML = `<div style="color:#d94f4f;padding:20px;">${err.message}</div>`;
        }
    });

    window._lastAnalyses = [];

    function renderAnalytics(analyses) {
        window._lastAnalyses = analyses;
        if (!analyses || analyses.length === 0) {
            modalBody.innerHTML = `
                <div style="text-align:center;padding:40px 20px;color:var(--color-text-tertiary);">
                    <div style="font-size:32px;margin-bottom:12px;">📭</div>
                    <div style="font-size:14px;">Henüz analiz yapılmamış.<br>İlk analizini yaptıktan sonra burada görünecek.</div>
                </div>`;
            return;
        }

        const labels = analyses.map((a, i) => a.tarih || `Analiz ${i+1}`);
        const matData = analyses.map(a => a.mat);
        const fizData = analyses.map(a => a.fiz);
        const kimData = analyses.map(a => a.kim);
        const genelData = analyses.map(a => a.genel);

        const last = analyses[analyses.length - 1];
        const first = analyses[0];
        const trend = analyses.length > 1 ? last.genel - first.genel : null;
        const trendHtml = trend !== null
            ? `<span style="color:${trend >= 0 ? '#1D9E75' : '#d94f4f'};font-weight:600;">${trend >= 0 ? '+' : ''}${trend} puan</span>`
            : '';

        modalBody.innerHTML = `
            <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
                <div style="flex:1;min-width:100px;background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">Toplam Analiz</div>
                    <div style="font-size:22px;font-weight:700;color:var(--color-text-primary);">${analyses.length}</div>
                </div>
                <div style="flex:1;min-width:100px;background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">Son Genel Ort.</div>
                    <div style="font-size:22px;font-weight:700;color:#1D9E75;">${last.genel}</div>
                </div>
                ${trend !== null ? `
                <div style="flex:1;min-width:100px;background:var(--color-background-secondary);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:var(--color-text-tertiary);margin-bottom:4px;">İlerleme</div>
                    <div style="font-size:22px;font-weight:700;">${trendHtml}</div>
                </div>` : ''}
            </div>
            <div style="background:var(--color-background-primary);border:1px solid rgba(0,0,0,0.08);border-radius:12px;padding:16px;margin-bottom:14px;">
                <div style="font-size:13px;font-weight:600;color:var(--color-text-primary);margin-bottom:12px;">Ders Ortalamaları Trendi</div>
                <canvas id="analyticsChart" height="200"></canvas>
            </div>
            <div style="background:var(--color-background-primary);border:1px solid rgba(0,0,0,0.08);border-radius:12px;padding:16px;">
                <div style="font-size:13px;font-weight:600;color:var(--color-text-primary);margin-bottom:10px;">Geçmiş Analizler</div>
                ${analyses.slice().reverse().map(a => `
                    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.06);font-size:12px;">
                        <div style="color:var(--color-text-tertiary);min-width:110px;">${a.tarih}</div>
                        <div style="color:#1D9E75;min-width:40px;">Mat: ${a.mat}</div>
                        <div style="color:#378ADD;min-width:40px;">Fiz: ${a.fiz}</div>
                        <div style="color:#D85A30;min-width:40px;">Kim: ${a.kim}</div>
                        <div style="color:var(--color-text-primary);font-weight:600;">Ort: ${a.genel}</div>
                        <button onclick="showPastAdvice(${a.id})" style="margin-left:auto;background:${a.ai ? '#e1f5ee' : '#f5f5f3'};color:${a.ai ? '#0f6e56' : '#aaa'};border:1px solid ${a.ai ? '#9fe1cb' : '#e0e0e0'};border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;cursor:${a.ai ? 'pointer' : 'default'};">${a.ai ? 'Tavsiyeleri Gör' : 'Tavsiye yok'}</button>
                    </div>`).join('')}
            </div>
        `;

        if (_analyticsChart) { _analyticsChart.destroy(); _analyticsChart = null; }
        const ctx = document.getElementById('analyticsChart');
        if (ctx) {
            // Chart.js canvas'a çizdiği için CSS değişkenlerini okuyamaz; temayı JS ile algıla.
            const _dark = document.documentElement.classList.contains('dark');
            const _txt  = _dark ? '#b3b2ad' : '#5f5e5a';
            const _grid = _dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';
            const _genel = _dark ? '#e7e7e4' : '#1a1a18';
            _analyticsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        { label: 'Genel', data: genelData, borderColor: _genel, backgroundColor: _dark ? 'rgba(231,231,228,0.06)' : 'rgba(26,26,24,0.05)', tension: 0.3, pointRadius: 4 },
                        { label: 'Matematik', data: matData, borderColor: '#1D9E75', backgroundColor: 'transparent', tension: 0.3, pointRadius: 3 },
                        { label: 'Fizik', data: fizData, borderColor: '#378ADD', backgroundColor: 'transparent', tension: 0.3, pointRadius: 3 },
                        { label: 'Kimya', data: kimData, borderColor: '#D85A30', backgroundColor: 'transparent', tension: 0.3, pointRadius: 3 },
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, color: _txt } } },
                    scales: {
                        y: { min: 0, max: 100, ticks: { font: { size: 11 }, color: _txt }, grid: { color: _grid } },
                        x: { ticks: { font: { size: 10 }, maxRotation: 30, color: _txt }, grid: { color: _grid } }
                    }
                }
            });
        }
    }
    window.showPastAdvice = (analysisId) => {
        const a = _lastAnalyses.find(x => x.id === analysisId);
        if (!a || !a.ai) return;
        const ai = a.ai;

        const dersKonfig = [
            { key: 'matematik', baslik: ai.matematikDurum, trend: ai.matematikTrend, tavsiyeler: ai.matematikTavsiyeler, renk: 'var(--acc-green-fg)', bg: 'var(--acc-green-bg)', border: 'var(--acc-green-bd)' },
            { key: 'fizik',     baslik: ai.fizikDurum,     trend: ai.fizikTrend,     tavsiyeler: ai.fizikTavsiyeler,     renk: 'var(--acc-red-fg)',   bg: 'var(--acc-red-bg)',   border: 'var(--acc-red-bd)' },
            { key: 'kimya',     baslik: ai.kimyaDurum,     trend: ai.kimyaTrend,     tavsiyeler: ai.kimyaTavsiyeler,     renk: 'var(--acc-amber-fg)', bg: 'var(--acc-amber-bg)', border: 'var(--acc-amber-bd)' },
        ];

        modalTitle.innerText = `Tavsiyeler — ${a.tarih}`;
        modalTitle.style.color = 'var(--color-text-primary)';
        modalDot.style.backgroundColor = '#1D9E75';

        modalBody.innerHTML = `
            <button onclick="renderAnalytics(window._lastAnalyses)" style="background:none;border:none;color:#1D9E75;font-size:12px;font-weight:600;cursor:pointer;padding:0 0 12px;display:flex;align-items:center;gap:4px;">← Analizlere Dön</button>
            <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
                <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px 14px;font-size:12px;"><span style="color:var(--color-text-tertiary);">Mat:</span> <b style="color:#1D9E75;">${a.mat}</b></div>
                <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px 14px;font-size:12px;"><span style="color:var(--color-text-tertiary);">Fiz:</span> <b style="color:#378ADD;">${a.fiz}</b></div>
                <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px 14px;font-size:12px;"><span style="color:var(--color-text-tertiary);">Kim:</span> <b style="color:#D85A30;">${a.kim}</b></div>
                <div style="background:var(--color-background-secondary);border-radius:8px;padding:10px 14px;font-size:12px;"><span style="color:var(--color-text-tertiary);">Genel:</span> <b>${a.genel}</b></div>
            </div>
            ${dersKonfig.map(d => `
            <div style="border:1px solid ${d.border};border-radius:10px;margin-bottom:12px;overflow:hidden;">
                <div style="background:${d.bg};padding:10px 14px;font-size:13px;font-weight:600;color:${d.renk};display:flex;justify-content:space-between;">
                    <span>${d.baslik || ''}</span>
                    <span style="font-weight:400;font-size:12px;">${d.trend || ''}</span>
                </div>
                <div style="padding:10px 14px;">
                    ${(d.tavsiyeler || []).map(t => `
                    <div style="display:flex;gap:8px;margin-bottom:8px;font-size:12px;line-height:1.5;color:var(--color-text-primary);">
                        <div style="width:6px;height:6px;border-radius:50%;background:${d.renk};flex-shrink:0;margin-top:5px;"></div>
                        <div>${t}</div>
                    </div>`).join('')}
                </div>
            </div>`).join('')}
        `;
    };
    // ── RAPORLAR SON ──────────────────────────────────────

    // ── PROFİL PANELİ ─────────────────────────────────────
    const profilePanel = document.getElementById('profilePanel');
    const profileBackdrop = document.getElementById('profileBackdrop');

    async function openProfile() {
        profileBackdrop.style.display = 'block';
        profilePanel.style.right = '0';
        try {
            const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
            const data = await res.json();
            const fullName = [data.ad, data.soyad].filter(Boolean).join(" ");
            const initials = fullName
                ? (data.ad[0] + (data.soyad ? data.soyad[0] : "")).toUpperCase()
                : (data.email || "?").slice(0, 2).toUpperCase();
            document.getElementById('profilePanelAvatar').innerText = initials;
            document.getElementById('profilePanelEmail').innerText = data.email || "";
            document.getElementById('profileAd').value = data.ad || "";
            document.getElementById('profileSoyad').value = data.soyad || "";
        } catch {}
        loadGoals();
    }

    function closeProfile() {
        profilePanel.style.right = '-420px';
        profileBackdrop.style.display = 'none';
    }

    document.getElementById('profileTrigger').addEventListener('click', e => {
        if (e.target.id === 'logoutBtn') return;
        openProfile();
    });
    document.getElementById('profileClose').addEventListener('click', closeProfile);
    document.getElementById('profileBackdrop').addEventListener('click', closeProfile);

    // ── TEMA (Karanlık Mod) ───────────────────────────────
    // <html>.dark sınıfı tüm temayı sürer; tercih localStorage'da saklanır.
    const THEME_KEY = 'eduai_theme';
    const themeIsDark = () => localStorage.getItem(THEME_KEY) === 'dark';
    function applyTheme(dark) { document.documentElement.classList.toggle('dark', dark); }
    function updateThemeUI() {
        const dark = themeIsDark();
        const lbl = document.getElementById('themeToggleLabel');
        const st  = document.getElementById('themeToggleState');
        if (lbl) lbl.innerText = dark ? '☀️ Aydınlık Mod' : '🌙 Karanlık Mod';
        if (st)  st.innerText  = dark ? 'Açık' : 'Kapalı';
    }
    document.getElementById('themeToggleBtn')?.addEventListener('click', () => {
        const next = !themeIsDark();
        localStorage.setItem(THEME_KEY, next ? 'dark' : 'light');
        applyTheme(next);
        updateThemeUI();
        // Not: Raporlar grafiği bir sonraki açılışında temaya göre yeniden çizilir.
    });
    applyTheme(themeIsDark());
    updateThemeUI();

    document.getElementById('logoutBtnPanel').addEventListener('click', () => {
        clearToken();
        window.location.replace('/login');
    });

    document.getElementById('deleteAccountBtn').addEventListener('click', async () => {
        if (!confirm('Hesabın ve tüm verilerin (hedefler, analizler) kalıcı olarak silinecek. Emin misin?')) return;
        const btn = document.getElementById('deleteAccountBtn');
        btn.disabled = true; btn.innerText = 'Siliniyor...';
        try {
            const res = await fetch(`${API_BASE}/auth/account`, {
                method: 'DELETE',
                headers: authHeaders()
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                alert(data.detail || 'Hesap silinemedi.');
                btn.disabled = false; btn.innerText = 'Hesabımı Sil';
                return;
            }
            clearToken();
            alert('Hesabın silindi.');
            window.location.replace('/login');
        } catch {
            alert('Sunucuya bağlanılamadı.');
            btn.disabled = false; btn.innerText = 'Hesabımı Sil';
        }
    });

    // Ad soyad kaydet
    document.getElementById('profileSaveBtn').addEventListener('click', async () => {
        const ad = document.getElementById('profileAd').value.trim();
        const soyad = document.getElementById('profileSoyad').value.trim();
        const msgEl = document.getElementById('profileSaveMsg');
        const btn = document.getElementById('profileSaveBtn');
        btn.disabled = true; btn.innerText = 'Kaydediliyor...';
        try {
            const res = await fetch(`${API_BASE}/auth/profile`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify({ ad, soyad })
            });
            const data = await res.json();
            if (!res.ok) { msgEl.style.color = '#d94f4f'; msgEl.innerText = data.detail || 'Hata.'; return; }
            msgEl.style.color = '#1D9E75';
            msgEl.innerText = 'Kaydedildi!';
            updateSidebarUser({ ad, soyad, email: document.getElementById('profilePanelEmail').innerText });
            document.getElementById('profilePanelAvatar').innerText = ad && soyad
                ? (ad[0] + soyad[0]).toUpperCase()
                : (ad || soyad || '?')[0].toUpperCase();
            setTimeout(() => { msgEl.innerText = ''; }, 3000);
        } catch { msgEl.style.color = '#d94f4f'; msgEl.innerText = 'Bağlanılamadı.'; }
        finally { btn.disabled = false; btn.innerText = 'Kaydet'; }
    });

    // Şifre değiştir
    document.getElementById('pwdSendCodeBtn').addEventListener('click', async () => {
        const current = document.getElementById('pwdCurrent').value;
        const next = document.getElementById('pwdNew').value;
        const errEl = document.getElementById('pwdError');
        errEl.style.color = '#d94f4f';
        errEl.innerText = '';
        if (!current || !next) { errEl.innerText = 'Önce mevcut ve yeni şifreyi doldurun.'; return; }
        const btn = document.getElementById('pwdSendCodeBtn');
        btn.disabled = true; btn.innerText = 'Gönderiliyor...';
        try {
            const res = await fetch(`${API_BASE}/auth/request-password-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() }
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) { errEl.innerText = data.detail || 'Kod gönderilemedi.'; return; }
            errEl.style.color = '#1D9E75';
            errEl.innerText = 'Kod e-postana gönderildi (5 dk geçerli).';
            document.getElementById('pwdCode').focus();
        } catch { errEl.innerText = 'Sunucuya bağlanılamadı.'; }
        finally { btn.disabled = false; btn.innerText = '📧 E-postama doğrulama kodu gönder'; }
    });

    document.getElementById('pwdSaveBtn').addEventListener('click', async () => {
        const current = document.getElementById('pwdCurrent').value;
        const next = document.getElementById('pwdNew').value;
        const code = document.getElementById('pwdCode').value.trim();
        const errEl = document.getElementById('pwdError');
        errEl.style.color = '#d94f4f';
        errEl.innerText = '';
        if (!current || !next) { errEl.innerText = 'Her iki alan zorunlu.'; return; }
        if (!code) { errEl.innerText = 'Önce e-postana gelen kodu girin.'; return; }
        const btn = document.getElementById('pwdSaveBtn');
        btn.disabled = true; btn.innerText = 'Kaydediliyor...';
        try {
            const res = await fetch(`${API_BASE}/auth/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify({ current_password: current, new_password: next, code })
            });
            const data = await res.json();
            if (!res.ok) { errEl.innerText = data.detail || 'Hata oluştu.'; return; }
            document.getElementById('pwdCurrent').value = '';
            document.getElementById('pwdNew').value = '';
            document.getElementById('pwdCode').value = '';
            errEl.style.color = '#1D9E75';
            errEl.innerText = 'Şifre güncellendi!';
            setTimeout(() => { errEl.innerText = ''; errEl.style.color = '#d94f4f'; }, 3000);
        } catch { errEl.innerText = 'Sunucuya bağlanılamadı.'; }
        finally { btn.disabled = false; btn.innerText = 'Şifreyi Güncelle'; }
    });
    // ── PROFİL PANELİ SON ─────────────────────────────────

    // ── HEDEFLERİM ────────────────────────────────────────

    async function loadGoals() {
        try {
            const res = await fetch(`${API_BASE}/api/goals`, { headers: authHeaders() });
            if (!res.ok) throw new Error("Hedefler alınamadı");
            const data = await res.json();
            renderGoals(data.goals);
        } catch (err) {
            modalBody.innerHTML = `<div style="color:#d94f4f;padding:20px;">${err.message}</div>`;
        }
    }

    function renderGoals(goals) {
        const tamamlanan = goals.filter(g => g.tamamlandi).length;
        modalBody.innerHTML = `
            <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input id="goalBaslik" type="text" placeholder="Hedef başlığı..." style="flex:1;border:1px solid rgba(0,0,0,0.18);border-radius:8px;padding:9px 12px;font-size:13px;outline:none;"/>
                <button id="goalEkleBtn" style="background:#F59E0B;color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;">+ Ekle</button>
            </div>
            <input id="goalAciklama" type="text" placeholder="Açıklama (isteğe bağlı)..." style="width:100%;border:1px solid rgba(0,0,0,0.18);border-radius:8px;padding:8px 12px;font-size:12px;outline:none;margin-bottom:16px;"/>
            ${goals.length > 0 ? `<div style="font-size:12px;color:var(--color-text-tertiary);margin-bottom:10px;">${tamamlanan}/${goals.length} tamamlandı</div>` : ''}
            <div id="goalsList">
                ${goals.length === 0 ? `
                    <div style="text-align:center;padding:30px;color:var(--color-text-tertiary);">
                        <div style="font-size:28px;margin-bottom:8px;">🎯</div>
                        <div>Henüz hedef eklenmedi.</div>
                    </div>` :
                goals.map(g => `
                    <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid rgba(0,0,0,0.07);">
                        <input type="checkbox" ${g.tamamlandi ? 'checked' : ''} data-id="${g.id}"
                            style="margin-top:3px;width:16px;height:16px;cursor:pointer;accent-color:#F59E0B;"
                            onchange="toggleGoal(${g.id}, this.checked)"/>
                        <div style="flex:1;">
                            <div style="font-size:13px;font-weight:500;color:var(--color-text-primary);${g.tamamlandi ? 'text-decoration:line-through;color:var(--color-text-tertiary);' : ''}">${g.baslik}</div>
                            ${g.aciklama ? `<div style="font-size:12px;color:var(--color-text-tertiary);margin-top:2px;">${g.aciklama}</div>` : ''}
                            <div style="font-size:11px;color:#bbb;margin-top:2px;">${g.tarih}</div>
                        </div>
                        <button onclick="deleteGoal(${g.id})" style="background:none;border:none;color:#ccc;cursor:pointer;font-size:16px;padding:0 4px;" title="Sil">🗑</button>
                    </div>`).join('')}
            </div>
        `;

        document.getElementById('goalEkleBtn').addEventListener('click', addGoal);
        document.getElementById('goalBaslik').addEventListener('keydown', e => { if (e.key === 'Enter') addGoal(); });
    }

    async function addGoal() {
        const baslik = document.getElementById('goalBaslik').value.trim();
        const aciklama = document.getElementById('goalAciklama').value.trim();
        if (!baslik) { document.getElementById('goalBaslik').focus(); return; }
        try {
            const res = await fetch(`${API_BASE}/api/goals`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify({ baslik, aciklama })
            });
            if (!res.ok) throw new Error();
            document.getElementById('goalBaslik').value = '';
            document.getElementById('goalAciklama').value = '';
            await loadGoals();
        } catch { alert('Hedef eklenemedi.'); }
    }

    window.toggleGoal = async (id, checked) => {
        await fetch(`${API_BASE}/api/goals/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ tamamlandi: checked ? 1 : 0 })
        });
        await loadGoals();
    };

    window.deleteGoal = async (id) => {
        if (!confirm('Bu hedefi silmek istediğine emin misin?')) return;
        await fetch(`${API_BASE}/api/goals/${id}`, { method: 'DELETE', headers: authHeaders() });
        await loadGoals();
    };
    // ── HEDEFLERİM SON ────────────────────────────────────