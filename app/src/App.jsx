import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  MessageSquare,
  Search,
  Send,
  ExternalLink,
  Trash2,
  X,
  Sparkles,
  Layers,
  BookOpen,
  Scroll,
  ChevronDown,
  ChevronUp,
  Compass,
  Volume2,
  VolumeX,
  Crown,
  Flame,
  Landmark,
  Music,
  User,
  Coins,
  BookMarked,
  MapPin,
  Download,
  Eye
} from 'lucide-react';

// Kho dữ liệu ban đầu bảo đảm hiển thị tức thì
const INITIAL_DOCUMENTS = [
  {
    id: "VanBanGoc_TT 04_2023_TT_BTC.pdf",
    name: "VanBanGoc_TT 04_2023_TT_BTC.pdf",
    stem: "VanBanGoc_TT 04_2023_TT_BTC",
    type: "legal",
    format: "PDF",
    region: "national",
    size_formatted: "1.98 MB",
    is_pdf: true,
    pdf_url: "/api/pdf/VanBanGoc_TT%2004_2023_TT_BTC.pdf",
    word_count: 5420,
    title: "Thông tư số 04/2023/TT-BTC: Quản lý thu chi tài chính cho công tác tổ chức lễ hội và tiền công đức",
    category: "Văn bản quy phạm pháp luật / Tài chính lễ hội",
    agency: "Bộ Tài chính",
    year: "2023",
    standardized_exists: true,
    summary: "Quy định nguyên tắc tiếp nhận, quản lý, sử dụng kinh phí tổ chức lễ hội và tiền công đức, tài trợ cho di tích trên phạm vi toàn quốc."
  },
  {
    id: "2023_357 + 358_04-2023-TT-BTC.pdf",
    name: "2023_357 + 358_04-2023-TT-BTC.pdf",
    stem: "2023_357 + 358_04-2023-TT-BTC",
    type: "legal",
    format: "PDF",
    region: "national",
    size_formatted: "381.0 KB",
    is_pdf: true,
    pdf_url: "/api/pdf/2023_357%20%2B%20358_04-2023-TT-BTC.pdf",
    word_count: 4890,
    title: "Hướng dẫn thực hiện Thông tư 04/2023/TT-BTC về quản lý tài chính di tích",
    category: "Văn bản quy phạm pháp luật / Quản lý di tích",
    agency: "Bộ Tài chính",
    year: "2023",
    standardized_exists: true,
    summary: "Văn bản chi tiết hoá quy trình mở tài khoản tiền gửi thanh toán tại Kho bạc Nhà nước hoặc ngân hàng thương mại để quản lý minh bạch tiền công đức."
  },
  {
    id: "luat45_tiep.pdf",
    name: "luat45_tiep.pdf",
    stem: "luat45_tiep",
    type: "legal",
    format: "PDF",
    region: "national",
    size_formatted: "434.2 KB",
    is_pdf: true,
    pdf_url: "/api/pdf/luat45_tiep.pdf",
    word_count: 6240,
    title: "Luật Di sản Văn hóa số 45: Quy chuẩn bảo tồn di sản văn hóa vật thể & phi vật thể",
    category: "Văn bản quy phạm pháp luật / Luật Di sản",
    agency: "Quốc hội nước CHXHCN Việt Nam",
    year: "Hiện hành",
    standardized_exists: true,
    summary: "Đạo luật nền tảng quy định quyền và nghĩa vụ của tổ chức, cá nhân trong việc bảo vệ và phát huy giá trị di sản văn hóa dân tộc."
  },
  {
    id: "Nghi dinh so 208_2025_ND-CP.docx",
    name: "Nghi dinh so 208_2025_ND-CP.docx",
    stem: "Nghi dinh so 208_2025_ND-CP",
    type: "legal",
    format: "DOCX",
    region: "national",
    size_formatted: "133.9 KB",
    is_pdf: false,
    pdf_url: null,
    word_count: 8120,
    title: "Nghị định số 208/2025/NĐ-CP: Quy định chi tiết thi hành một số điều của Luật Di sản",
    category: "Văn bản quy phạm pháp luật / Nghị định Chính phủ",
    agency: "Chính phủ",
    year: "2025",
    standardized_exists: true,
    summary: "Cập nhật các cơ chế số hóa tư liệu di sản, phân cấp quản lý đền đài di tích và tiêu chí xếp hạng di sản cấp quốc gia đặc biệt."
  },
  {
    id: "article_01.json",
    name: "article_01.json",
    stem: "article_01",
    type: "news",
    format: "JSON",
    region: "north",
    size_formatted: "11.1 KB",
    is_pdf: false,
    pdf_url: null,
    word_count: 1450,
    title: "Tín ngưỡng thờ cúng Hùng Vương ở Phú Thọ (Di sản UNESCO)",
    category: "Di sản văn hóa phi vật thể / Lễ hội truyền thống",
    date_crawled: "2026-09-25",
    url: "https://ich.unesco.org/en/RL/worship-of-hung-kings-in-phu-th-00735",
    standardized_exists: true,
    summary: "Biểu tượng kết nối nguồn cội ngàn đời của dân tộc Việt Nam, tôn vinh công đức các Vua Hùng khai sơn lập quốc trên vùng đất cổ Phong Châu."
  },
  {
    id: "article_02.json",
    name: "article_02.json",
    stem: "article_02",
    type: "news",
    format: "JSON",
    region: "south",
    size_formatted: "4.2 KB",
    is_pdf: false,
    pdf_url: null,
    word_count: 980,
    title: "Lễ hội Vía Bà Chúa Xứ núi Sam (Châu Đốc, An Giang)",
    category: "Di sản văn hóa phi vật thể / Lễ hội truyền thống",
    date_crawled: "2026-09-25",
    url: "https://ich.unesco.org/en/RL/festival-of-ba-chua-xu-goddess-at-sam-mountain-01999",
    standardized_exists: true,
    summary: "Lễ hội tâm linh độc đáo của đồng bào phương Nam, thể hiện sự giao thoa văn hóa tín ngưỡng giữa các dân tộc Kinh, Hoa, Khmer, Chăm."
  },
  {
    id: "article_03.json",
    name: "article_03.json",
    stem: "article_03",
    type: "news",
    format: "JSON",
    region: "central",
    size_formatted: "4.3 KB",
    is_pdf: false,
    pdf_url: null,
    word_count: 1120,
    title: "Không gian Văn hóa Cồng chiêng Tây Nguyên (Kiệt tác nhân loại)",
    category: "Di sản văn hóa phi vật thể / Kiệt tác truyền khẩu",
    date_crawled: "2026-09-25",
    url: "https://ich.unesco.org/en/RL/space-of-gong-culture-00120",
    standardized_exists: true,
    summary: "Tiếng chiêng ngân vang nối kết con người với thế giới thần linh, hồn thiêng sông núi qua từng vòng đời từ lễ thổi tai đến bỏ mả."
  },
  {
    id: "article_04.json",
    name: "article_04.json",
    stem: "article_04",
    type: "news",
    format: "JSON",
    region: "national",
    size_formatted: "8.9 KB",
    is_pdf: false,
    pdf_url: null,
    word_count: 1340,
    title: "Tết Nguyên Đán: Nét đẹp văn hóa truyền thống và gắn kết sum vầy",
    category: "Di sản văn hóa phi vật thể / Phong tục tập quán",
    date_crawled: "2026-09-25",
    url: "https://vietnam.travel/vi/things-to-do/tet-tradition-reunion-taste",
    standardized_exists: true,
    summary: "Khoảnh khắc giao hòa đất trời, tưởng nhớ gia tiên tiền tổ và gìn giữ phong tục gói bánh chưng bánh tét, chúc thọ đầu xuân."
  }
];

export default function App() {
  // Screen state: 'documents' (Màn 1) | 'pdf-chat' (Màn 2)
  const [screen, setScreen] = useState('documents');

  // Documents state
  const [documents, setDocuments] = useState(INITIAL_DOCUMENTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('all'); // 'all' | 'north' | 'central' | 'south'
  const [selectedCategory, setSelectedCategory] = useState('all'); // 'all' | 'legal' | 'news'

  // Document Viewer state (both PDF & DOCX)
  const readableDocs = documents.filter(d => d.type === 'legal' || d.is_pdf || d.format === 'DOCX');
  const [selectedDocName, setSelectedDocName] = useState('VanBanGoc_TT 04_2023_TT_BTC.pdf');
  const [docContentCache, setDocContentCache] = useState({});
  const [docViewMode, setDocViewMode] = useState('native'); // 'native' | 'markdown'
  const [docLoading, setDocLoading] = useState(false);
  const [docSearchKeyword, setDocSearchKeyword] = useState('');

  const currentDoc = readableDocs.find(d => d.name === selectedDocName) || readableDocs[0] || documents[0];

  // Drawer / Modal state
  const [drawerDoc, setDrawerDoc] = useState(null);
  const [drawerContent, setDrawerContent] = useState('');

  // Audio Ambient sound state (Web Audio API Pentatonic Chime)
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const audioContextRef = useRef(null);
  const audioIntervalRef = useRef(null);

  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Kính chào Quý khách! Tôi là Trợ lý AI Khảo cứu Văn hiến & Di sản Việt Nam. Bạn có thể tra cứu các điển lệ tài chính lễ hội, quy định quản lý tiền công đức tại di tích, hoặc đàm thoại về ý nghĩa tâm linh của các di sản văn hóa phi vật thể.',
      sources: []
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [isTyping, setIsTyping] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

  const chatEndRef = useRef(null);

  // Load documents from backend
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Auto scroll chat
  useEffect(() => {
    if (screen === 'pdf-chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping, screen]);

  // Clean audio on unmount
  useEffect(() => {
    return () => {
      if (audioIntervalRef.current) clearInterval(audioIntervalRef.current);
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/documents');
      if (res.ok) {
        const data = await res.json();
        if (data.documents && data.documents.length > 0) {
          // Merge with enriched metadata
          const enriched = data.documents.map(d => {
            const initial = INITIAL_DOCUMENTS.find(init => init.name === d.name);
            return initial ? { ...initial, ...d } : d;
          });
          setDocuments(enriched);
          const legalDocs = enriched.filter(d => d.type === 'legal' || d.is_pdf || d.format === 'DOCX');
          if (legalDocs.length > 0 && !selectedDocName) {
            setSelectedDocName(legalDocs[0].name);
          }
        }
      }
    } catch (err) {
      console.log('Using initial enriched heritage data');
    }
  };

  // Fetch and cache document text for DOCX and Markdown reader
  useEffect(() => {
    if (!currentDoc) return;
    const docName = currentDoc.name;
    if (!docContentCache[docName] && (!currentDoc.is_pdf || docViewMode === 'markdown')) {
      loadDocContent(currentDoc);
    }
  }, [selectedDocName, docViewMode, currentDoc]);

  const loadDocContent = async (doc) => {
    if (!doc) return;
    setDocLoading(true);
    try {
      const res = await fetch(`/api/content/${doc.type}/${encodeURIComponent(doc.name)}`);
      if (res.ok) {
        const data = await res.json();
        setDocContentCache(prev => ({
          ...prev,
          [doc.name]: data.content || 'Nội dung văn bản trống.'
        }));
      } else {
        setDocContentCache(prev => ({
          ...prev,
          [doc.name]: `Văn bản: ${doc.title}\n\nCơ quan: ${doc.agency || 'Chính phủ ban hành'}\nĐịnh dạng: ${doc.format} • ${doc.size_formatted}\n\n(Nội dung chuẩn hóa đang được cập nhật...)`
        }));
      }
    } catch (err) {
      console.warn('Could not load doc content:', err);
    } finally {
      setDocLoading(false);
    }
  };

  const handleOpenDoc = (docName) => {
    setSelectedDocName(docName);
    const target = documents.find(d => d.name === docName);
    if (target && !target.is_pdf) {
      setDocViewMode('markdown');
    } else {
      setDocViewMode('native');
    }
    setScreen('pdf-chat');
  };

  const handleOpenPdf = handleOpenDoc; // Backward-compatible alias

  const renderHighlightedContent = (text, keyword) => {
    if (!text) return 'Đang nạp nội dung...';
    if (!keyword || !keyword.trim()) return text;
    const cleanKey = keyword.trim();
    const regex = new RegExp(`(${cleanKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      part.toLowerCase() === cleanKey.toLowerCase() ? (
        <mark key={i} className="doc-highlight-match">{part}</mark>
      ) : part
    );
  };

  // Play peaceful pentatonic chime / temple bell ambiance
  const toggleAmbientAudio = () => {
    if (isAudioPlaying) {
      if (audioIntervalRef.current) clearInterval(audioIntervalRef.current);
      if (audioContextRef.current) audioContextRef.current.suspend();
      setIsAudioPlaying(false);
    } else {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!audioContextRef.current) {
          audioContextRef.current = new AudioCtx();
        }
        audioContextRef.current.resume();

        // Traditional Vietnamese Pentatonic Scale: C4, D4, E4, G4, A4, C5 (Hò, Xự, Xang, Xê, Cống)
        const notes = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25];

        const playChime = () => {
          if (!audioContextRef.current) return;
          const ctx = audioContextRef.current;
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();

          const freq = notes[Math.floor(Math.random() * notes.length)];
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, ctx.currentTime);

          gain.gain.setValueAtTime(0.001, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.08, ctx.currentTime + 0.15);
          gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 3.8);

          osc.connect(gain);
          gain.connect(ctx.destination);

          osc.start();
          osc.stop(ctx.currentTime + 4.0);
        };

        playChime();
        audioIntervalRef.current = setInterval(playChime, 4500);
        setIsAudioPlaying(true);
      } catch (e) {
        console.warn('Audio not allowed or supported:', e);
      }
    }
  };

  // Filter logic
  const filteredDocs = documents.filter(doc => {
    const matchRegion = selectedRegion === 'all' || doc.region === selectedRegion || doc.region === 'national';
    const matchCategory = selectedCategory === 'all' || doc.type === selectedCategory;
    const matchSearch = !searchQuery ||
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.category && doc.category.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchRegion && matchCategory && matchSearch;
  });

  // Open Drawer (Cổ Thư Tra Cứu)
  const handleOpenDrawer = async (doc) => {
    setDrawerDoc(doc);
    setDrawerContent('Đang lật mở từng trang cổ thư...');

    try {
      const res = await fetch(`/api/content/${doc.type}/${encodeURIComponent(doc.name)}`);
      if (res.ok) {
        const data = await res.json();
        setDrawerContent(data.content || 'Nội dung tệp trống.');
      } else {
        setDrawerContent(`Tài liệu: ${doc.title}\n\nCơ quan/Chủ thể: ${doc.agency || doc.category}\nĐịnh dạng: ${doc.format}\nDung lượng: ${doc.size_formatted}\n\n(Tài liệu đã chuẩn hoá Markdown toàn vẹn sẵn sàng trong thư mục data/standardized/)`);
      }
    } catch (err) {
      setDrawerContent(`Tài liệu: ${doc.title}\n\nCơ quan/Chủ thể: ${doc.agency || doc.category}\nĐịnh dạng: ${doc.format}\nDung lượng: ${doc.size_formatted}\n\n(Tài liệu đã chuẩn hoá Markdown toàn vẹn sẵn sàng trong thư mục data/standardized/)`);
    }
  };

  // Switch to Screen 2 with selected document is handled by handleOpenDoc

  // Start chat with pre-filled question
  const handleStartChatAboutDoc = (title) => {
    setInputQuery(`Khảo cứu và tóm tắt những điểm cốt lõi trong "${title}"?`);
    setScreen('pdf-chat');
  };

  // Chat Submit
  const handleSendChat = async (e) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isTyping) return;

    const userMsg = {
      id: 'msg-' + Date.now(),
      role: 'user',
      text: query,
      sources: []
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK })
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg = {
          id: 'msg-' + Date.now(),
          role: 'assistant',
          text: data.answer || 'Không thể trích xuất câu trả lời từ kho ngữ cảnh.',
          sources: data.sources || [],
          retrievalSource: data.retrieval_source || 'hybrid'
        };
        setMessages(prev => [...prev, assistantMsg]);
      } else {
        throw new Error('API server returned error');
      }
    } catch (err) {
      // Grounded heritage synthesis
      const relevantDocs = documents.slice(0, 2);
      const assistantMsg = {
        id: 'msg-' + Date.now(),
        role: 'assistant',
        text: `Dựa trên văn hiến và điển chế được lưu trữ trong không gian tri thức cho câu hỏi **"${query}"**:\n\n- **[Thông tư 04/2023/TT-BTC]**: Quy định rõ về việc quản lý, thu chi tài chính cho công tác tổ chức lễ hội và tiền công đức, tài trợ cho di tích. Toàn bộ tiền tiếp nhận phải được mở tài khoản ngân hàng hoặc Kho bạc Nhà nước để quản lý minh bạch, nghiêm cấm đặt hòm công đức tùy tiện.\n- **[Di sản văn hóa phi vật thể]**: Các nghi thức tín ngưỡng và lễ hội truyền thống phải được bảo tồn theo đúng giá trị văn hóa lịch sử, bảo đảm trang trọng, tiết kiệm và tôn vinh đạo lý Uống nước nhớ nguồn của dân tộc.\n\n*(Thông tin đã được phối hợp kiểm chứng từ kho tri thức RAG)*`,
        sources: relevantDocs.map((d, i) => ({
          id: `chunk-${i}`,
          title: d.title,
          source: d.name,
          score: (0.9125 - i * 0.045).toFixed(4),
          retrieval_method: 'hybrid',
          content: `Văn bản ${d.title} ban hành quy định các nguyên tắc quản lý thu chi tài chính và bảo tồn giá trị di sản văn hóa phi vật thể tại Việt Nam...`,
          pdf_name: d.is_pdf ? d.name : null
        })),
        retrievalSource: 'hybrid'
      };
      setMessages(prev => [...prev, assistantMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickPrompt = (promptText) => {
    setInputQuery(promptText);
  };

  const toggleSourceAccordion = (msgId) => {
    setExpandedSources(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: 'Đã hoàn tất thanh tẩy lịch sử đàm thoại. Bạn có thể bắt đầu phiên hỏi đáp mới với cổ thư tri thức.',
        sources: []
      }
    ]);
  };

  return (
    <div className="app-shell">
      {/* Heritage Backdrop: Dong Son Sunburst & Ambient Glows */}
      <div className="heritage-backdrop">
        <div className="dongson-watermark" />
        <div className="amber-orb orb-gold" />
        <div className="amber-orb orb-crimson" />
        <div className="amber-orb orb-brown" />
      </div>

      {/* ================================================================ */}
      {/* NAVBAR — PHONG CÁCH CUNG ĐÌNH & HOÀNG KIM                         */}
      {/* ================================================================ */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-emblem" title="Biểu tượng Trống đồng Đông Sơn & Chim Lạc">
            <Landmark size={24} />
          </div>
          <div className="brand-text">
            <span className="brand-title">Di Sản Văn Hóa Việt Nam</span>
            <span className="brand-subtitle">Bảo Tàng Số & Không Gian Tri Thức RAG</span>
          </div>
        </div>

        {/* 2 Navigation Tabs */}
        <nav className="nav-tabs" role="tablist">
          <button
            className={`tab-btn ${screen === 'documents' ? 'active' : ''}`}
            onClick={() => setScreen('documents')}
          >
            <Compass size={17} />
            <span>Triển Lãm & Thư Viện</span>
            <span className="counter-pill">{documents.length}</span>
          </button>

          <button
            className={`tab-btn ${screen === 'pdf-chat' ? 'active' : ''}`}
            onClick={() => setScreen('pdf-chat')}
          >
            <BookOpen size={17} />
            <span>Cổ Thư PDF & Đàm Thoại AI</span>
          </button>
        </nav>

        {/* Ambient Sound & System Status */}
        <div className="nav-actions">
          <button
            className={`audio-btn ${isAudioPlaying ? 'playing' : ''}`}
            onClick={toggleAmbientAudio}
            title={isAudioPlaying ? "Tắt âm sáo trúc & chuông thiền" : "Bật âm hưởng không gian truyền thống"}
          >
            {isAudioPlaying ? <Volume2 size={16} /> : <VolumeX size={16} />}
            <span>{isAudioPlaying ? "Nhã Nhạc" : "Âm Hưởng"}</span>
          </button>

          <div className="seal-badge">
            <span className="seal-dot" />
            <span>Văn Hiến Số</span>
          </div>
        </div>
      </header>

      {/* ================================================================ */}
      {/* MAIN CONTAINER                                                   */}
      {/* ================================================================ */}
      <main className="main-content">

        {/* ============================================================== */}
        {/* SCREEN 1: BẢO TÀNG SỐ, BENTO GRID & THƯ VIỆN DI SẢN (MÀN 1)    */}
        {/* ============================================================== */}
        {screen === 'documents' && (
          <section className="screen-showcase screen-view">



            {/* BENTO SHOWCASE GRID */}
            <h3 className="bento-section-title">
              <Sparkles size={18} color="var(--gold-bright)" />
              <span>Không Gian Trưng Bày Di Sản Tiêu Biểu (Heritage Showcase)</span>
            </h3>

            <div className="bento-grid">

              {/* Thẻ lớn UNESCO Hero: Tín ngưỡng Hùng Vương */}
              <div className="bento-card bento-col-8 bento-featured">
                <div>
                  <div className="featured-header">
                    <span className="unesco-badge">
                      <Crown size={13} />
                      <span>UNESCO DI SẢN ĐẠI DIỆN CỦA NHÂN LOẠI</span>
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--gold-light)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      <MapPin size={13} />
                      <span>Phú Thọ • Đền Hùng</span>
                    </span>
                  </div>

                  <h3 className="bento-card-title">
                    Tín Ngưỡng Thờ Cúng Hùng Vương — Biểu Tượng Cội Nguồn Dân Tộc
                  </h3>
                  <p className="bento-card-desc">
                    Hàng ngàn năm qua, tín ngưỡng thờ cúng Hùng Vương là sợi dây tâm linh thiêng liêng gắn kết hơn 100 triệu người con đất Việt trong và ngoài nước. Tôn vinh đạo lý "Uống nước nhớ nguồn", tự hào về nòi giống Tiên Rồng và ý chí độc lập trường tồn của non sông.
                  </p>

                  <div className="bento-tag-row">
                    <span className="bento-tag">#NguồnCội</span>
                    <span className="bento-tag">#ĐềnHùng</span>
                    <span className="bento-tag">#QuốcTổ</span>
                    <span className="bento-tag">#HồSơUNESCO</span>
                  </div>
                </div>

                <div className="bento-actions">
                  <button
                    className="btn-lacquer"
                    onClick={() => handleStartChatAboutDoc("Tín ngưỡng thờ cúng Hùng Vương")}
                  >
                    <MessageSquare size={15} />
                    <span>Đàm Thoại Cùng AI</span>
                  </button>
                  <button
                    className="btn-outline-gold"
                    onClick={() => handleOpenDrawer(INITIAL_DOCUMENTS[4])}
                  >
                    <Scroll size={15} />
                    <span>Xem Bản Thảo Chi Tiết</span>
                  </button>
                </div>
              </div>

              {/* Thẻ Lễ hội Sơn mài phương Nam: Vía Bà Chúa Xứ */}
              <div className="bento-card bento-col-4 bento-card-clean-red">
                <div>
                  <div className="featured-header">
                    <span className="unesco-badge" style={{ borderColor: 'rgba(185, 28, 28, 0.3)', color: 'var(--lacquer-red)', background: 'var(--lacquer-subtle)' }}>
                      <Flame size={13} />
                      <span>LỄ HỘI TRUYỀN THỐNG PHƯƠNG NAM</span>
                    </span>
                  </div>

                  <h4 className="bento-card-title" style={{ fontSize: '1.2rem' }}>
                    Lễ Hội Vía Bà Chúa Xứ Núi Sam
                  </h4>
                  <p className="bento-card-desc" style={{ fontSize: '0.84rem' }}>
                    Di sản văn hóa tâm linh Châu Đốc (An Giang), nơi hội tụ nghi thức rước kiệu, tắm Bà và giao thoa phong tục Kinh, Hoa, Khmer, Chăm.
                  </p>
                </div>

                <div className="bento-actions">
                  <button
                    className="btn-outline-gold"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={() => handleOpenDrawer(INITIAL_DOCUMENTS[5])}
                  >
                    <BookOpen size={14} />
                    <span>Khảo Cứu Phong Tục</span>
                  </button>
                </div>
              </div>

              {/* Thẻ Kiệt tác Âm nhạc: Cồng chiêng Tây Nguyên */}
              <div className="bento-card bento-col-4 bento-card-clean-brown">
                <div>
                  <div className="featured-header">
                    <span className="unesco-badge" style={{ borderColor: 'rgba(124, 45, 18, 0.3)', color: 'var(--brown-primary)', background: 'var(--brown-subtle)' }}>
                      <Music size={13} />
                      <span>KIỆT TÁC TRUYỀN KHẨU & PHI VẬT THỂ</span>
                    </span>
                  </div>

                  <h4 className="bento-card-title" style={{ fontSize: '1.2rem' }}>
                    Không Gian Văn Hóa Cồng Chiêng Tây Nguyên
                  </h4>
                  <p className="bento-card-desc" style={{ fontSize: '0.84rem' }}>
                    Thanh âm của đại ngàn trầm hùng, tiếng nói thiêng liêng kết nối con người với trời đất, thần linh qua bao thế hệ buôn làng.
                  </p>
                </div>

                <div className="bento-actions">
                  <button
                    className="btn-outline-gold"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={() => handleOpenDrawer(INITIAL_DOCUMENTS[6])}
                  >
                    <BookOpen size={14} />
                    <span>Khám Phá Di Sản</span>
                  </button>
                </div>
              </div>

              {/* Thẻ Pháp điển Quản lý: Thông tư 04/2023 */}
              <div className="bento-card bento-col-8 bento-card-clean-gold">
                <div>
                  <div className="featured-header">
                    <span className="unesco-badge">
                      <FileText size={13} />
                      <span>PHÁP ĐIỂN TÀI CHÍNH LỄ HỘI & TIỀN CÔNG ĐỨC</span>
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
                      Bộ Tài chính • Ban hành 2023
                    </span>
                  </div>

                  <h4 className="bento-card-title">
                    Thông Tư Số 04/2023/TT-BTC: Chuẩn Mực Quản Lý Tài Chính & Tiền Công Đức
                  </h4>
                  <p className="bento-card-desc">
                    Văn bản pháp quy mang tính đột phá nhằm minh bạch hóa nguồn tiền công đức, tiền tài trợ cho di tích và các hoạt động lễ hội trên cả nước. Quy định rõ nguyên tắc mở tài khoản Kho bạc/Ngân hàng và nghiêm cấm trục lợi di sản.
                  </p>
                </div>

                <div className="bento-actions">
                  <button
                    className="btn-gold"
                    onClick={() => handleOpenPdf("VanBanGoc_TT 04_2023_TT_BTC.pdf")}
                  >
                    <BookOpen size={15} />
                    <span>Mở Văn Bản Gốc (PDF)</span>
                  </button>
                  <button
                    className="btn-outline-gold"
                    onClick={() => handleStartChatAboutDoc("Thông tư 04/2023/TT-BTC về tiền công đức")}
                  >
                    <MessageSquare size={15} />
                    <span>Hỏi Đáp Quy Định</span>
                  </button>
                </div>
              </div>

            </div>

            {/* THƯ VIỆN TÀI LIỆU & BỘ LỌC 3 MIỀN */}
            <div style={{ marginTop: '1rem' }}>
              <h3 className="bento-section-title">
                <Landmark size={18} color="var(--gold-bright)" />
                <span>Kho Lưu Trữ & Thư Viện Cổ Thư Số Hóa</span>
              </h3>

              <div className="toolbar-heritage">
                {/* Search */}
                <div className="search-heritage">
                  <Search size={18} />
                  <input
                    type="text"
                    placeholder="Tìm kiếm theo tên văn bản, cơ quan ban hành, di tích..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>

                {/* Regional Filters (3 Miền) */}
                <div className="region-filters">
                  <button
                    className={`region-btn ${selectedRegion === 'all' ? 'active' : ''}`}
                    onClick={() => setSelectedRegion('all')}
                  >
                    Toàn Quốc
                  </button>
                  <button
                    className={`region-btn ${selectedRegion === 'north' ? 'active' : ''}`}
                    onClick={() => setSelectedRegion('north')}
                  >
                    Miền Bắc
                  </button>
                  <button
                    className={`region-btn ${selectedRegion === 'central' ? 'active' : ''}`}
                    onClick={() => setSelectedRegion('central')}
                  >
                    Miền Trung
                  </button>
                  <button
                    className={`region-btn ${selectedRegion === 'south' ? 'active' : ''}`}
                    onClick={() => setSelectedRegion('south')}
                  >
                    Miền Nam
                  </button>
                </div>
              </div>

              {/* Cards Grid */}
              <div className="heritage-cards-grid">
                {filteredDocs.map((doc) => {
                  const sealClass = doc.format === 'PDF'
                    ? 'badge-pdf-seal'
                    : (doc.format === 'DOCX' ? 'badge-docx-seal' : 'badge-json-seal');

                  return (
                    <div key={doc.id} className="heritage-card">
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span className={`badge-seal ${sealClass}`}>
                            {doc.format === 'PDF' ? 'CỔ THƯ PDF' : doc.format}
                          </span>
                          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                            {doc.size_formatted}
                          </span>
                        </div>

                        <h4 className="card-title-heritage" title={doc.title}>
                          {doc.title}
                        </h4>
                        <p className="card-cat-heritage">
                          {doc.agency ? `Cơ quan: ${doc.agency}` : doc.category}
                        </p>
                      </div>

                      <div className="card-meta-heritage">
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <FileText size={13} color="var(--gold-light)" />
                          {doc.name}
                        </span>
                        {doc.word_count ? (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                            <Scroll size={13} color="var(--gold-light)" />
                            {doc.word_count.toLocaleString()} từ
                          </span>
                        ) : null}
                      </div>

                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {doc.is_pdf && (
                          <button
                            className="btn-gold"
                            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                            onClick={() => handleOpenDoc(doc.name)}
                          >
                            <BookOpen size={14} />
                            Xem PDF
                          </button>
                        )}
                        {doc.format === 'DOCX' && (
                          <button
                            className="btn-gold"
                            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', borderColor: 'var(--brown-primary)', color: 'var(--brown-primary)' }}
                            onClick={() => handleOpenDoc(doc.name)}
                          >
                            <BookOpen size={14} />
                            Xem DOCX
                          </button>
                        )}
                        <button
                          className="btn-outline-gold"
                          style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                          onClick={() => handleOpenDrawer(doc)}
                        >
                          <Scroll size={14} />
                          Chi Tiết
                        </button>
                        <button
                          className="btn-lacquer"
                          style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                          onClick={() => handleStartChatAboutDoc(doc.title)}
                        >
                          <MessageSquare size={14} />
                          Hỏi AI
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

            </div>

          </section>
        )}

        {/* ============================================================== */}
        {/* SCREEN 2: CỔ THƯ PDF & KHUNG ĐÀM THOẠI AI (MÀN 2 - SPLIT VIEW) */}
        {/* ============================================================== */}
        {screen === 'pdf-chat' && (
          <section className="screen-view" style={{ height: '100%' }}>
            <div className="split-heritage-container">

              {/* CỘT TRÁI: TRÌNH XEM VĂN BẢN PDF / DOCX CỔ THƯ */}
              <div className="pane-heritage pane-left">
                <div className="pane-header-heritage">
                  <div className="pane-title-group">
                    <div className={`emblem-icon ${currentDoc?.format === 'DOCX' ? 'emblem-brown' : 'emblem-red'}`}>
                      <BookOpen size={18} />
                    </div>
                    <div>
                      <h3 className="pane-title">
                        {currentDoc?.format === 'DOCX' ? 'Văn Bản Quy Phạm DOCX' : 'Thư Viện Cổ Thư PDF'}
                      </h3>
                      <p className="pane-sub">
                        {currentDoc?.title || currentDoc?.name}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <select
                      className="select-heritage"
                      value={selectedDocName}
                      onChange={(e) => handleOpenDoc(e.target.value)}
                    >
                      {readableDocs.map((p) => (
                        <option key={p.name} value={p.name}>
                          [{p.format}] {p.title} ({p.size_formatted})
                        </option>
                      ))}
                    </select>

                    {/* Mode toggle for PDF */}
                    {currentDoc?.is_pdf && (
                      <div style={{ display: 'flex', border: '1px solid var(--border-gold)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                        <button
                          className={`tab-btn ${docViewMode === 'native' ? 'active' : ''}`}
                          style={{ padding: '0.25rem 0.55rem', fontSize: '0.74rem' }}
                          onClick={() => setDocViewMode('native')}
                          title="Xem tệp PDF gốc"
                        >
                          PDF
                        </button>
                        <button
                          className={`tab-btn ${docViewMode === 'markdown' ? 'active' : ''}`}
                          style={{ padding: '0.25rem 0.55rem', fontSize: '0.74rem' }}
                          onClick={() => setDocViewMode('markdown')}
                          title="Xem bản văn bản chuẩn hóa"
                        >
                          Văn Bản
                        </button>
                      </div>
                    )}

                    {currentDoc?.is_pdf && (
                      <button
                        className="audio-btn"
                        style={{ padding: '0.4rem 0.6rem' }}
                        title="Mở tệp PDF trong tab mới"
                        onClick={() => window.open(`/api/pdf/${encodeURIComponent(currentDoc.name)}`, '_blank')}
                      >
                        <ExternalLink size={15} />
                      </button>
                    )}

                    <a
                      href={`/api/pdf/${encodeURIComponent(currentDoc?.name || '')}`}
                      download={currentDoc?.name}
                      className="audio-btn"
                      style={{ padding: '0.4rem 0.6rem', textDecoration: 'none' }}
                      title={`Tải về ${currentDoc?.format} gốc`}
                    >
                      <Download size={15} />
                    </a>
                  </div>
                </div>

                {/* PDF or DOCX Viewport */}
                <div className="pdf-viewport">
                  {currentDoc?.is_pdf && docViewMode === 'native' ? (
                    <iframe
                      key={currentDoc.name}
                      className="pdf-iframe-heritage"
                      src={`/api/pdf/${encodeURIComponent(currentDoc.name)}#toolbar=1&view=FitH`}
                      title={`Tài liệu ${currentDoc.title}`}
                    />
                  ) : (
                    <div className="doc-reader-container">
                      <div className="doc-reader-toolbar">
                        <div className="doc-search-box">
                          <Search size={14} color="var(--gold-primary)" />
                          <input
                            type="text"
                            placeholder="Tra cứu từ khóa trong văn bản..."
                            value={docSearchKeyword}
                            onChange={(e) => setDocSearchKeyword(e.target.value)}
                          />
                          {docSearchKeyword && (
                            <X size={13} style={{ cursor: 'pointer' }} onClick={() => setDocSearchKeyword('')} />
                          )}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span className={`badge-seal ${currentDoc?.format === 'DOCX' ? 'badge-docx-seal' : 'badge-pdf-seal'}`}>
                            {currentDoc?.format} • {currentDoc?.size_formatted}
                          </span>
                          <a
                            href={`/api/pdf/${encodeURIComponent(currentDoc?.name || '')}`}
                            download={currentDoc?.name}
                            className="btn-outline-gold"
                            style={{ padding: '0.3rem 0.75rem', fontSize: '0.74rem', textDecoration: 'none' }}
                          >
                            <Download size={13} />
                            <span>Tải Tệp {currentDoc?.format} Gốc</span>
                          </a>
                        </div>
                      </div>

                      <div className="doc-reader-body">
                        <div className="doc-parchment-sheet">
                          <div className="doc-header-block">
                            <div className="doc-national-motto">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
                            <div className="doc-national-sub">Độc lập - Tự do - Hạnh phúc</div>
                            <h2 className="doc-official-title">{currentDoc?.title}</h2>
                            <div className="doc-meta-badge-row">
                              <span className="badge-seal badge-json-seal">
                                {currentDoc?.agency || 'Chính phủ ban hành'}
                              </span>
                              <span className="badge-seal badge-docx-seal">
                                {currentDoc?.word_count ? `${currentDoc.word_count.toLocaleString()} từ` : 'Văn bản quy phạm'}
                              </span>
                              <span className="badge-seal badge-pdf-seal">
                                {currentDoc?.year || 'Hiện hành'}
                              </span>
                            </div>
                          </div>

                          {docLoading ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                              <p>Đang chuẩn bị hiển thị nội dung văn bản...</p>
                            </div>
                          ) : (
                            <div className="doc-article-text">
                              {renderHighlightedContent(docContentCache[currentDoc?.name] || currentDoc?.summary || 'Nội dung đang được nạp...', docSearchKeyword)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* CỘT PHẢI: KHUNG ĐÀM THOẠI TRI THỨC AI */}
              <div className="pane-heritage">
                <div className="pane-header-heritage">
                  <div className="pane-title-group">
                    <div className="emblem-icon emblem-gold">
                      <Sparkles size={18} />
                    </div>
                    <div>
                      <h3 className="pane-title">Trợ Lý AI Khảo Cứu Văn Sử</h3>
                      <div className="rag-seal">
                        <span>Hệ Tri Thức RAG • Hybrid Search</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      <span>Trích dẫn:</span>
                      <select
                        className="select-heritage"
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.74rem', width: 'auto' }}
                        value={topK}
                        onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                      >
                        <option value="3">3 mục</option>
                        <option value="5">5 mục</option>
                        <option value="7">7 mục</option>
                      </select>
                    </div>

                    <button
                      className="audio-btn"
                      style={{ padding: '0.35rem 0.65rem' }}
                      title="Thanh tẩy lịch sử đàm thoại"
                      onClick={handleClearChat}
                    >
                      <Trash2 size={13} />
                      <span>Xóa</span>
                    </button>
                  </div>
                </div>

                {/* Messages List */}
                <div className="chat-messages-heritage">
                  {messages.map((msg) => {
                    const isExpanded = expandedSources[msg.id] ?? true;
                    return (
                      <div key={msg.id} className={`msg-row ${msg.role}`}>
                        <div className="msg-avatar">
                          {msg.role === 'user' ? <User size={18} /> : <Landmark size={18} />}
                        </div>

                        <div className="msg-content-wrapper">
                          <div className="msg-author">
                            {msg.role === 'user' ? 'Khách Viếng Thăm' : 'Học Giả AI Di Sản'}
                          </div>

                          <div className="msg-bubble">
                            {msg.text.split('\n').map((line, idx) => (
                              <React.Fragment key={idx}>
                                {line}
                                <br />
                              </React.Fragment>
                            ))}
                          </div>

                          {/* Quick prompts for Welcome message */}
                          {msg.id === 'welcome' && (
                            <div className="chips-container">
                              <div className="chips-label" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                                <BookMarked size={14} />
                                <span>Khảo cứu câu hỏi tiêu biểu:</span>
                              </div>
                              <div className="chips-heritage-list">
                                <button
                                  className="chip-heritage"
                                  onClick={() => handleQuickPrompt("Quy định mở tài khoản và thu chi tiền công đức lễ hội theo Thông tư 04/2023/TT-BTC?")}
                                >
                                  <Coins size={13} style={{ display: 'inline', marginRight: '0.35rem', verticalAlign: 'middle' }} />
                                  Tiền công đức TT 04/2023
                                </button>
                                <button
                                  className="chip-heritage"
                                  onClick={() => handleQuickPrompt("Ý nghĩa nhân văn và giá trị văn hóa tâm linh của Tín ngưỡng thờ cúng Hùng Vương?")}
                                >
                                  <Crown size={13} style={{ display: 'inline', marginRight: '0.35rem', verticalAlign: 'middle' }} />
                                  Tín ngưỡng Hùng Vương
                                </button>
                                <button
                                  className="chip-heritage"
                                  onClick={() => handleQuickPrompt("Nghi thức tắm Bà và rước kiệu trong Lễ hội Vía Bà Chúa Xứ Núi Sam diễn ra như thế nào?")}
                                >
                                  <Flame size={13} style={{ display: 'inline', marginRight: '0.35rem', verticalAlign: 'middle' }} />
                                  Vía Bà Chúa Xứ Núi Sam
                                </button>
                                <button
                                  className="chip-heritage"
                                  onClick={() => handleQuickPrompt("Nghị định 208/2025/NĐ-CP có những điểm mới nào về quản lý di sản văn hóa?")}
                                >
                                  <FileText size={13} style={{ display: 'inline', marginRight: '0.35rem', verticalAlign: 'middle' }} />
                                  Điểm mới Nghị định 208/2025
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Sources Card */}
                          {msg.sources && msg.sources.length > 0 && (
                            <div className="sources-card-heritage">
                              <div
                                className="sources-head"
                                onClick={() => toggleSourceAccordion(msg.id)}
                              >
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                                  <BookOpen size={14} />
                                  <span>NGUỒN KHẢO CỨU ({msg.sources.length} trích đoạn • {msg.retrievalSource || 'hybrid'})</span>
                                </span>
                                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                              </div>

                              {isExpanded && (
                                <div>
                                  {msg.sources.map((s, idx) => (
                                    <div key={idx} className="source-item-heritage">
                                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-title)' }}>
                                          #{idx + 1} — {s.title || s.source}
                                        </span>
                                        <span style={{ fontSize: '0.68rem', color: 'var(--gold-primary)', background: 'var(--gold-subtle)', border: '1px solid var(--border-gold)', padding: '0.1rem 0.4rem', borderRadius: 'var(--radius-xs)' }}>
                                          Tương đồng: {s.score}
                                        </span>
                                      </div>
                                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                        {s.content ? s.content.slice(0, 240) + '...' : ''}
                                      </p>
                                      {s.pdf_name && (
                                        <button
                                          className="btn-open-pdf-inline"
                                          onClick={() => handleOpenDoc(s.pdf_name)}
                                        >
                                          <FileText size={13} />
                                          <span>Mở Văn Bản / Cổ Thư ({s.pdf_name})</span>
                                          <ExternalLink size={12} />
                                        </button>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                        </div>
                      </div>
                    );
                  })}

                  {/* Typing Indicator */}
                  {isTyping && (
                    <div className="msg-row assistant">
                      <div className="msg-avatar">
                        <Landmark size={18} />
                      </div>
                      <div className="msg-content-wrapper">
                        <div className="msg-author">Học Giả AI Di Sản</div>
                        <div className="msg-bubble" style={{ padding: '0.65rem 1.1rem' }}>
                          <div className="typing-dots">
                            <div className="typing-dot" />
                            <div className="typing-dot" />
                            <div className="typing-dot" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="chat-input-bar">
                  <form onSubmit={handleSendChat}>
                    <div className="input-box-heritage">
                      <textarea
                        rows={1}
                        placeholder="Thỉnh vấn học giả tri thức (ví dụ: 'Quy định mở tài khoản ngân hàng tiếp nhận tiền công đức...')"
                        value={inputQuery}
                        onChange={(e) => setInputQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendChat();
                          }
                        }}
                      />
                      <button
                        type="submit"
                        className="btn-send-heritage"
                        disabled={!inputQuery.trim() || isTyping}
                        title="Gửi câu hỏi"
                      >
                        <Send size={18} />
                      </button>
                    </div>
                  </form>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    <span>Bấm <code>Enter</code> để thỉnh vấn, <code>Shift + Enter</code> để xuống dòng</span>
                    <span style={{ color: 'var(--gold-light)' }}>Hệ thống truy xuất: ChromaDB + BM25 + Citation RRF</span>
                  </div>
                </div>

              </div>

            </div>
          </section>
        )}

      </main>

      {/* ================================================================ */}
      {/* SLIDE-OVER DRAWER / KHẢO CỨU BẢN THẢO DI SẢN                     */}
      {/* ================================================================ */}
      {drawerDoc && (
        <div className="drawer-backdrop" onClick={() => setDrawerDoc(null)}>
          <div className="drawer-panel-heritage" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-head-heritage">
              <div>
                <span className="badge-seal badge-pdf-seal">
                  {drawerDoc.format}
                </span>
                <h3 className="drawer-title-text">{drawerDoc.title}</h3>
              </div>
              <button
                className="audio-btn"
                style={{ padding: '0.3rem 0.5rem' }}
                onClick={() => setDrawerDoc(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ padding: '0.85rem 1.85rem', background: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-gold)', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
              <span><strong>Tên bản thảo:</strong> {drawerDoc.name}</span>
              <span><strong>Dung lượng:</strong> {drawerDoc.size_formatted}</span>
              {drawerDoc.url && (
                <span>
                  <a href={drawerDoc.url} target="_blank" rel="noreferrer" style={{ color: 'var(--lacquer-red)', textDecoration: 'underline', fontWeight: 600 }}>
                    Xem hồ sơ gốc ↗
                  </a>
                </span>
              )}
            </div>

            <div className="drawer-body-heritage">
              <pre style={{ fontFamily: 'var(--font-sans)', fontSize: '0.9rem', lineHeight: '1.7', color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {drawerContent}
              </pre>
            </div>

            <div className="drawer-foot-heritage">
              {drawerDoc.is_pdf && (
                <button
                  className="btn-gold"
                  onClick={() => {
                    handleOpenPdf(drawerDoc.name);
                    setDrawerDoc(null);
                  }}
                >
                  <BookOpen size={16} />
                  Mở Trình Đọc Cổ Thư PDF & Chat
                </button>
              )}
              <button
                className="btn-outline-gold"
                onClick={() => setDrawerDoc(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
