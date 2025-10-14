import { useEffect, useState } from "react";
import DOMPurify from "dompurify";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [mails, setMails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [desiredRole, setDesiredRole] = useState("");
  const [savingRole, setSavingRole] = useState(false);
  const [showRolePanel, setShowRolePanel] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("email"); // "email" or "analysis"

  const fetchEmails = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:5000/emails", { credentials: "include" });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) setMails(data);
      else if (data && Array.isArray(data.emails)) setMails(data.emails);
      else setMails([]);
    } catch (err) {
      console.error("Failed to fetch emails:", err);
      setError(err.message || String(err));
      setMails([]);
    } finally {
      setLoading(false);
    }
  };

  const triggerRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await fetch("http://localhost:5000/fetch-new-emails", {
        method: "POST",
        credentials: "include"
      });

      if (!res.ok) throw new Error(`Failed to trigger refresh: ${res.status}`);

      const data = await res.json();
      console.log("✅ Refresh triggered:", data);

      setTimeout(() => {
        fetchEmails();
        setRefreshing(false);
      }, 3000);

    } catch (err) {
      console.error("Failed to trigger refresh:", err);
      alert("Failed to fetch new emails. Make sure you're logged in.");
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  useEffect(() => {
    if (mails.length === 0) {
      setSelectedIndex(0);
    } else if (selectedIndex >= mails.length) {
      setSelectedIndex(0);
    }
  }, [mails, selectedIndex]);

  // Reset to email tab when changing emails
  useEffect(() => {
    setActiveTab("email");
  }, [selectedIndex]);

  const currentMail = mails[selectedIndex];
  const hasAnalysis = currentMail?.processed && currentMail?.agentAnalysis;

  return (
    <div className="h-screen flex flex-col bg-[#57707a] text-slate-50 overflow-hidden">

      {/* Mobile top bar */}
      <header className="sm:hidden bg-transparent border-b border-slate-700 p-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            aria-label="Toggle sidebar"
            className="p-2 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-800"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            ☰
          </button>
          <h1 className="text-lg font-semibold text-white">Raven AI</h1>
        </div>
        <button
          className="bg-indigo-600 text-white px-3 py-1 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={triggerRefresh}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Sidebar */}
        <aside
          className={`${sidebarOpen ? "block" : "hidden"} sm:flex w-64 bg-[#1e293b] text-slate-50 flex-col shrink-0 h-full`}
          aria-label="Mailbox folders"
        >
          <div className="p-4 font-bold text-lg border-b border-slate-700 flex items-center justify-between shrink-0">
            <span>📧 Mails</span>
            <button
              className="hidden sm:inline bg-indigo-600 px-2 py-1 rounded hover:bg-indigo-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={triggerRefresh}
              disabled={refreshing}
            >
              {refreshing ? "⏳" : "🔄"}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 min-h-0">
            <button
              onClick={() => setShowRolePanel(true)}
              className="w-full mb-3 px-4 py-3 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition flex items-center justify-center gap-2 font-medium"
            >
              <span>🎯</span>
              <span>Set Desired Role</span>
            </button>

            <ul role="listbox" className="flex flex-col gap-1">
              {mails.map((m, i) => (
                <li
                  key={m.id ?? i}
                  role="option"
                  tabIndex={0}
                  aria-selected={selectedIndex === i}
                  onClick={() => setSelectedIndex(i)}
                  onKeyDown={(e) => { if (e.key === 'Enter') setSelectedIndex(i); }}
                  className={`p-3 rounded-md cursor-pointer select-none transition-colors relative ${selectedIndex === i
                    ? "bg-slate-700 text-white"
                    : "hover:bg-slate-700/50 text-slate-200"
                    }`}
                >
                  <div className="font-medium truncate">{m.subject ?? m.title}</div>
                  <div className="text-sm text-slate-300 truncate">{m.from ?? "(No sender)"}</div>
                  {m.processed && m.agentAnalysis && (
                    <div className="absolute top-2 right-2">
                      <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">
                        ✓ AI
                      </span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-h-0 bg-transparent">

          {/* Mail header with tabs */}
          <div className="bg-slate-900 border-b border-slate-700">
            <div className="p-4 flex items-center justify-between">
              <h1 className="text-2xl font-extrabold text-indigo-400">
                Raven AI
              </h1>
            </div>

            {/* Tabs */}
            {mails.length > 0 && (
              <div className="flex gap-1 px-4">
                <button
                  onClick={() => setActiveTab("email")}
                  className={`px-4 py-2 font-medium transition-colors ${activeTab === "email"
                    ? "text-indigo-400 border-b-2 border-indigo-400"
                    : "text-slate-400 hover:text-slate-300"
                    }`}
                >
                  📧 Email
                </button>
                <button
                  onClick={() => setActiveTab("analysis")}
                  disabled={!hasAnalysis}
                  className={`px-4 py-2 font-medium transition-colors relative ${activeTab === "analysis"
                    ? "text-indigo-400 border-b-2 border-indigo-400"
                    : hasAnalysis
                      ? "text-slate-400 hover:text-slate-300"
                      : "text-slate-600 cursor-not-allowed"
                    }`}
                >
                  🤖 AI Analysis
                  {hasAnalysis && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6 bg-transparent">
            <div className="card-3d-wrapper">
              <article className="card-3d max-w-3xl mx-auto p-6">
                {mails.length === 0 ? (
                  <div className="text-slate-100 p-6 text-center">
                    {loading ? (
                      <div className="space-y-3">
                        <div className="text-4xl">⏳</div>
                        <div>Loading emails...</div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="text-4xl">📭</div>
                        <div>No emails found.</div>
                        <div>
                          Please{" "}
                          <a
                            className="underline text-indigo-400 hover:text-indigo-300"
                            href="http://localhost:5000/login"
                          >
                            login with Gmail
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    {/* Email Tab Content */}
                    {activeTab === "email" && (
                      <div className="space-y-6">
                        {/* Job Header Card */}
                        <div className="bg-gradient-to-r from-slate-50 to-slate-100 border border-slate-200 rounded-lg p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                                {currentMail?.jobTitle || currentMail?.subject}
                              </h2>
                              {currentMail?.jobCompany && (
                                <div className="flex items-center gap-2 text-slate-700 mb-2">
                                  <span className="text-lg">🏢</span>
                                  <span className="font-semibold">{currentMail.jobCompany}</span>
                                </div>
                              )}
                              {currentMail?.jobLocation && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <span>📍</span>
                                  <span>{currentMail.jobLocation}</span>
                                </div>
                              )}
                            </div>
                            {currentMail?.processed && (
                              <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                                ✓ Analyzed
                              </div>
                            )}
                          </div>

                          {currentMail?.jobUrl && (
                            <a
                              href={currentMail.jobUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition font-medium"
                            >
                              <span>🔗</span>
                              <span>View Original Posting</span>
                            </a>
                          )}
                        </div>

                        {/* Job Description */}
                        {currentMail?.jobPageContent && currentMail.jobPageContent.length > 100 ? (
                          <div className="bg-white border border-slate-200 rounded-lg p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                              <span>📄</span>
                              <span>Job Description</span>
                            </h3>
                            <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed whitespace-pre-wrap">
                              {currentMail.jobPageContent}
                            </div>
                          </div>
                        ) : currentMail?.bodyHtml ? (
                          <div className="bg-white border border-slate-200 rounded-lg p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                              <span>📧</span>
                              <span>Email Content</span>
                            </h3>
                            <div
                              className="prose prose-slate max-w-none text-slate-700 leading-relaxed"
                              dangerouslySetInnerHTML={{
                                __html: DOMPurify.sanitize(currentMail.bodyHtml, {
                                  ALLOWED_TAGS: ['a', 'b', 'i', 'strong', 'em', 'p', 'br', 'ul', 'ol', 'li', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img', 'table', 'tr', 'td', 'th', 'thead', 'tbody'],
                                  ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'target', 'rel', 'class', 'style', 'width', 'height'],
                                  ADD_ATTR: ['target'],
                                  ADD_DATA_URI_TAGS: ['img']
                                })
                              }}
                            />
                          </div>
                        ) : (
                          <div className="bg-white border border-slate-200 rounded-lg p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                              <span>📧</span>
                              <span>Email Content</span>
                            </h3>
                            <div className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                              {currentMail?.body}
                            </div>
                          </div>
                        )}

                        {/* Email Metadata */}
                        <div className="text-sm text-slate-500 border-t border-slate-200 pt-4">
                          <div>From: {currentMail?.from}</div>
                          <div>Subject: {currentMail?.subject}</div>
                        </div>
                      </div>
                    )}

                    {/* AI Analysis Tab Content */}
                    {activeTab === "analysis" && (
                      <div className="space-y-6">
                        {!hasAnalysis ? (
                          <div className="text-center py-12 space-y-4">
                            <div className="text-6xl">🤖</div>
                            <div className="text-xl font-semibold text-slate-900">
                              Analysis Pending
                            </div>
                            <div className="text-slate-600">
                              AI is processing this job posting...
                            </div>
                            <div className="animate-pulse text-slate-400">
                              This usually takes a few seconds
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                              <div className="flex items-center gap-3 mb-4">
                                <div className="text-3xl">🤖</div>
                                <div>
                                  <div className="font-bold text-indigo-900 text-lg">
                                    AI Career Advisor
                                  </div>
                                  <div className="text-sm text-indigo-600">
                                    Powered by AWS Bedrock (Claude Sonnet 4)
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="prose prose-slate max-w-none">
                              <div
                                className="text-slate-800 leading-relaxed space-y-4"
                                style={{
                                  whiteSpace: 'pre-wrap',
                                  wordBreak: 'break-word'
                                }}
                              >
                                {currentMail.agentAnalysis.split('\n').map((line, idx) => {
                                  // Handle bold markdown-style text
                                  if (line.startsWith('**') && line.endsWith('**')) {
                                    const text = line.slice(2, -2);
                                    return (
                                      <div key={idx} className="font-bold text-lg text-slate-900 mt-4">
                                        {text}
                                      </div>
                                    );
                                  }

                                  // Handle bullet points
                                  if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                                    return (
                                      <div key={idx} className="ml-4 text-slate-700">
                                        {line}
                                      </div>
                                    );
                                  }

                                  // Handle empty lines
                                  if (line.trim() === '') {
                                    return <div key={idx} className="h-2"></div>;
                                  }

                                  // Regular text
                                  return (
                                    <div key={idx} className="text-slate-800">
                                      {line}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                            <div className="mt-6 pt-6 border-t border-slate-200">
                              <div className="flex items-center justify-between">
                                <div className="text-sm text-slate-500">
                                  Analyzed on {new Date(currentMail.processedAt || Date.now()).toLocaleString()}
                                </div>
                                {currentMail.jobUrl && (
                                  <a
                                    href={currentMail.jobUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition font-medium"
                                  >
                                    Apply Now →
                                  </a>
                                )}
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}
              </article>
            </div>
          </div>

        </main>
      </div>

      {/* Overlay */}
      {showRolePanel && (
        <div
          onClick={() => setShowRolePanel(false)}
          className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm z-40"
        />
      )}

      {/* Slide-Out Role Panel */}
      <div
        className={`fixed top-0 left-0 h-full w-96 bg-[#1e293b] text-slate-50 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 ${showRolePanel ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        <div className="flex justify-between items-center p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold">Set Your Desired Role</h2>
          <button
            onClick={() => setShowRolePanel(false)}
            className="text-slate-400 hover:text-white text-2xl leading-none"
          >
            ✕
          </button>
        </div>

        <div className="p-4 space-y-3">
          <textarea
            rows="5"
            placeholder="Describe your desired role, e.g., 'ML/AI Engineer with Python and AWS experience'"
            value={desiredRole}
            onChange={(e) => setDesiredRole(e.target.value)}
            className="w-full p-3 rounded-md bg-slate-700 text-white placeholder:text-slate-400 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />

          <button
            onClick={async () => {
              setSavingRole(true);
              try {
                await fetch("http://localhost:5000/user/desiredRole", {
                  method: "POST",
                  credentials: "include",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ desiredRole }),
                });
                setShowRolePanel(false);
                alert("✅ Desired role saved! AI will use this for future job recommendations.");
              } catch (err) {
                console.error("Failed to save desired role:", err);
                alert("❌ Failed to save role. Please try again.");
              } finally {
                setSavingRole(false);
              }
            }}
            disabled={savingRole || !desiredRole.trim()}
            className="w-full py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {savingRole ? "Saving..." : "Save Role"}
          </button>
        </div>
      </div>
    </div>
  );
}