"use strict";

// The server sends only allowlisted participant material. No answer key belongs here.
const COPY = {
  ja: {
    title:"文脈と応答の評価", welcome:"はじめる前に", footer:"この端末内で保存します。モデル結果や想定ラベルは表示しません。",
    intro:"これは、研究著者本人による開発用の評価です。第三者による独立評価ではありません。課題文・候補文は英語の原文のまま表示します。",
    guide:"問題文を読み、その文脈からどの候補文が導かれるかを判断してください。研究の狙いやモデルの答えを推測せず、あなた自身の読みを記録してください。",
    bounds:"分からない・曖昧・どちらも違う、という判断も大切な回答です。途中で休んだり、回答を控えたりできます。",
    privacy:"外部通信・解析サービスは使いません。回答と訂正履歴はこのMacに保存します。保存した回答は同じURLから再開できます。確定後も想定回答は表示されません。",
    count:n=>`全${n}問。同じ課題の別条件は、この最初の評価では繰り返しません。`,
    english:"英語の課題文を読むときの自己評価", exposure:"この研究の課題・結果をこれまで見たことはありますか？", choose:"選択してください",
    comfortable:"無理なく読める", sometimes_difficult:"ときどき難しい", difficult:"かなり難しい", prefer_not_to_say:"回答を控える", yes:"はい", no:"いいえ", unsure:"はっきりしない",
    agree:"説明を読みました。著者として参加し、自分の判断を記録します。", prepare:"説明を確認して進む", start:"評価を開始", resume:"評価を再開",
    item:n=>`問題 ${n}`, progress:(done,total)=>`保存済み ${done} / ${total}`, first:"候補1", second:"候補2", question:"この文脈から導かれる候補は？",
    choices:[
      ["first","候補1","候補1のみが導かれる。"],["second","候補2","候補2のみが導かれる。"],
      ["both","両方","同じ読みのもとで、両方の候補が導かれる。"],["neither","どちらでもない","理解できるが、どちらの候補も導かれない。"],
      ["ambiguous","曖昧","複数の自然な読みがあり、読み方によって判断が変わる。"],["unclear","理解・判断困難","文の意味や状況が十分つかめず、判断できない。"],
      ["abstain","回答を控える","この項目には回答しない。理由の記入は任意。"]],
    recognition:"この課題やよく似た課題に見覚えはありますか？（任意）", note:"気づいたこと・迷った理由（任意）", optional:"自然さ・読みやすさを記録する（任意）", prompt:"問題文", good:"自然で理解しやすい", awkward:"理解できるが不自然", unclear:"意味をつかみにくい", unrated:"評価しない",
    previous:"前へ", save:"保存して次へ", saveLast:"保存して確認へ", skip:"未保存のまま次へ", review:"回答一覧・確定", discard:"保存していない入力があります。変更を破棄して移動しますか？",
    required:"判断を選んでください。「回答を控える」も選べます。", saved:"回答を保存しました。", pending:"入力はまだ保存されていません。下の保存ボタンを押してください。", breakdown:(answered,abstained,missing)=>`判断の記録 ${answered}件・回答を控える ${abstained}件・未回答 ${missing}件`,
    summary:"回答の確認", summaryGuide:"番号から戻って確認・訂正できます。下線のある番号は保存済みです。ここには正誤やモデルとの一致を表示しません。",
    remaining:n=>`未回答は${n}問です。未回答のまま確定する場合は、その理由を記録してください。`, reason:"未回答を残す理由", lockCheck:"この段階の回答を確定し、以後はこの画面から変更しません。", finalize:"回答を確定", locked:"回答を確定しました", lockedText:"回答は変更不可の記録として保存されました。答え合わせや、別の候補文の比較はまだ開始しません。以下から回答記録を保存できます。",
    export:"回答記録をダウンロード", back:"問題へ戻る", finalizeMissing:"確認欄と、必要な場合は未回答の理由を入力してください。", retry:"同じ操作を再送", reconnect:"接続できませんでした。入力を残しています。サーバーを確認し、同じ操作を再送してください。", conflict:"別の画面で記録が更新されています。入力は残しています。最新状態を確認してから保存し直してください。", refresh:"最新状態を読み込む", busy:"保存中…", loadFail:"読み込めませんでした。ローカルサーバーが動いているか確認してください。", setupRequired:"自己評価・事前の露出・確認欄を入力してください。"
  },
  en: {
    title:"Context and response assessment", welcome:"Before you begin", footer:"Saved on this device. Model results and intended labels are not displayed.",
    intro:"This is a development assessment by the research author, not an independent third-party evaluation. Task and response text stays in the original English.",
    guide:"Read the task and judge which response follows from its context. Record your own reading without trying to reconstruct the study hypothesis or the model's answer.",
    bounds:"Unclear, ambiguous, and neither are valid judgments. You may pause or decline to answer an item.",
    privacy:"No external communication or analytics service is used. Responses and revision history are saved on this Mac. Resume saved responses at this same URL. Finalizing does not reveal intended answers.",
    count:n=>`${n} items. This first assessment does not repeat alternative conditions of the same scenario.`,
    english:"How comfortable are you reading the English task text?", exposure:"Have you previously seen this study's tasks or results?", choose:"Choose an option",
    comfortable:"Comfortable", sometimes_difficult:"Sometimes difficult", difficult:"Quite difficult", prefer_not_to_say:"Prefer not to say", yes:"Yes", no:"No", unsure:"Unsure",
    agree:"I have read the instructions. I am participating as the author and will record my own judgments.", prepare:"Confirm and continue", start:"Begin assessment", resume:"Resume assessment",
    item:n=>`Item ${n}`, progress:(done,total)=>`Saved ${done} / ${total}`, first:"Response 1", second:"Response 2", question:"Which response follows from this context?",
    choices:[
      ["first","Response 1","Only response 1 follows."],["second","Response 2","Only response 2 follows."],
      ["both","Both","Both responses follow under the same reading."],["neither","Neither","I understand the task, but neither response follows."],
      ["ambiguous","Ambiguous","Several natural readings lead to different judgments."],["unclear","Unclear","I cannot understand the text or situation well enough to judge."],
      ["abstain","Decline to answer","I am not answering this item. A reason is optional."]],
    recognition:"Do you recognize this task or a closely related task? (optional)", note:"Observations or reasons for uncertainty (optional)", optional:"Record naturalness and comprehensibility (optional)", prompt:"Task text", good:"Natural and understandable", awkward:"Understandable but awkward", unclear:"Hard to understand", unrated:"Not rated",
    previous:"Previous", save:"Save and next", saveLast:"Save and review", skip:"Next without saving", review:"Review and finalize", discard:"You have unsaved input. Discard these changes and navigate?",
    required:"Choose a judgment. You can also decline to answer.", saved:"Response saved.", pending:"Input is not saved yet. Use the save button below.", breakdown:(answered,abstained,missing)=>`${answered} judgments · ${abstained} declined · ${missing} unanswered`,
    summary:"Review responses", summaryGuide:"Select an item number to review or revise it. Underlined numbers have saved responses. No correctness or model-agreement feedback is shown.",
    remaining:n=>`${n} items remain unanswered. To finalize with missing responses, record a reason.`, reason:"Reason for leaving items unanswered", lockCheck:"Finalize this phase's responses; they can no longer be edited in this interface.", finalize:"Finalize responses", locked:"Responses finalized", lockedText:"Your responses are saved as a locked record. Answer comparison and alternative-response panels have not begun. You can download your response record below.",
    export:"Download response record", back:"Back to items", finalizeMissing:"Confirm finalization and, if needed, give a reason for missing responses.", retry:"Retry the same operation", reconnect:"Connection failed. Your input is retained. Check the server and retry the same operation.", conflict:"Another page updated the record. Your input is retained. Review the latest state before saving again.", refresh:"Load latest state", busy:"Saving…", loadFail:"Unable to load. Check that the local server is running.", setupRequired:"Complete the self-report, prior-exposure question, and confirmation."
  }
};

let language = "ja", packet, state, position = 0, view = "intro", dirty = false, busy = false, pendingRequest = null;
const app = document.querySelector("#app"), notice = document.querySelector("#notice");
const t = () => COPY[language];
const el = (tag, text, className) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; };
const button = (text, action, className) => { const b=el("button",text,className); b.type="button"; b.addEventListener("click",action); return b; };
function say(text, error=false, retry=null) { notice.replaceChildren(el("span",text)); notice.className=error?"error":""; if(retry) notice.append(button(t().retry,retry)); }
function clearNotice() { notice.replaceChildren(); notice.className=""; }
function markDirty() { dirty=true; say(t().pending); }
function canLeave() { return !busy && !pendingRequest && (!dirty || window.confirm(t().discard)); }
function move(nextView, index=position) { if(!canLeave()) return; dirty=false; view=nextView; position=index; clearNotice(); render(); window.scrollTo(0,0); }
function selectField(name, label, values, value="") {
  const wrap=el("label",label,"field"), select=el("select"); select.name=name;
  for(const [v,txt] of [["",t().choose],...values]) { const o=el("option",txt); o.value=v; select.append(o); }
  select.value=value; wrap.append(select); return wrap;
}
function radioGroup(name, title, choices, selected, compact=false) {
  const set=el("fieldset"), group=el("div",undefined,compact?"compact":"choices"); set.append(el("legend",title));
  for(const [value,label,help] of choices) {
    const wrap=el("label",undefined,"choice"), input=el("input"); input.type="radio"; input.name=name; input.value=value; input.checked=selected===value;
    const texts=el("span"); texts.append(el("span",label,"choice-title")); if(help) texts.append(el("small",help)); wrap.append(input,texts); group.append(wrap);
  }
  set.append(group); return set;
}
function downloadLink() { const a=el("a",t().export,"download"); a.href="/api/export"; a.download="responses.json"; return a; }
async function readJSON(path) {
  const r=await fetch(path,{credentials:"same-origin",cache:"no-store"}); if(!r.ok) throw new Error("read_failed"); return r.json();
}
async function submit(path, payload, onSuccess) {
  if(busy || pendingRequest) return;
  pendingRequest={path, body:{...payload,request_id:crypto.randomUUID(),revision:state.revision,instruction_language:language}, onSuccess};
  await sendPending();
}
async function sendPending() {
  if(busy || !pendingRequest) return;
  busy=true; app.querySelectorAll("button,input,select,textarea").forEach(n=>n.disabled=true); document.querySelector("#language").disabled=true;
  say(t().busy);
  try {
    const request=pendingRequest;
    const res=await fetch(request.path,{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify(request.body)});
    const result=await res.json();
    if(!res.ok) {
      if(res.status===409 && result.state) state=result.state;
      pendingRequest=null;
      say(res.status===409?t().conflict:(result.message||result.error||"Request rejected"),true);
      return;
    }
    state=result; pendingRequest=null; dirty=false; request.onSuccess();
  } catch (_) { say(t().reconnect,true,sendPending); }
  finally {
    busy=false; document.querySelector("#language").disabled=Boolean(pendingRequest);
    app.querySelectorAll("button,input,select,textarea").forEach(n=>n.disabled=Boolean(pendingRequest));
    if(view==="item" && position===0) { const prev=document.querySelector("[data-prev]"); if(prev) prev.disabled=true; }
  }
}
function intro() {
  const c=t(); app.append(el("h1",c.welcome),el("p",c.intro),el("p",c.count(packet.total_items)),el("p",c.guide),el("p",c.bounds),el("p",c.privacy,"muted"));
  const examples=el("details"); examples.append(el("summary",c.question)); const ul=el("ul");
  for(const [,label,help] of c.choices) ul.append(el("li",`${label} — ${help}`)); examples.append(ul); app.append(examples);
  if(state.started) { app.append(button(c.resume,()=>move("item",firstUnanswered()),"primary")); return; }
  const form=el("form");
  form.append(selectField("english_confidence",c.english,["comfortable","sometimes_difficult","difficult","prefer_not_to_say"].map(k=>[k,c[k]]),state.setup?.english_confidence));
  form.append(selectField("prior_exposure",c.exposure,["yes","no","unsure"].map(k=>[k,c[k]]),state.setup?.prior_exposure));
  const agree=el("label",undefined,"check-line"), check=el("input"); check.type="checkbox"; check.name="agree"; agree.append(check,el("span",c.agree)); form.append(agree);
  const start=el("button",c.prepare,"primary"); start.type="submit"; form.append(start);
  form.addEventListener("input",()=>{dirty=true;});
  form.addEventListener("submit",async e=>{
    e.preventDefault(); const fd=new FormData(form);
    if(!fd.get("english_confidence")||!fd.get("prior_exposure")||!fd.get("agree")) { say(c.setupRequired,true); return; }
    await submit("/api/setup",{setup:{english_confidence:fd.get("english_confidence"),prior_exposure:fd.get("prior_exposure")}},()=>{
      // Start is a separate, explicit lifecycle event after successful setup.
      view="ready"; render(); clearNotice();
    });
  }); app.append(form);
}
function firstUnanswered() { const i=packet.items.findIndex(x=>!state.responses[x.id]); return i<0?0:i; }
function item() {
  const c=t(), data=packet.items[position], old=state.responses[data.id]||{};
  const bar=el("div",undefined,"toolbar spread"); bar.append(el("p",c.progress(Object.keys(state.responses).length,packet.total_items),"progress"),button(c.review,()=>move("review")));
  const heading=el("h1",c.item(position+1)); app.append(bar,heading,el("div",data.prompt,"prompt"));
  const candidates=el("div",undefined,"candidates");
  data.responses.forEach((text,i)=>{ const row=el("div",undefined,"candidate"); row.append(el("strong",i===0?c.first:c.second),el("p",text)); candidates.append(row); });
  app.append(candidates);
  const form=el("form"); form.append(radioGroup("choice",c.question,c.choices,old.choice));
  form.append(radioGroup("recognition",c.recognition,["yes","no","unsure"].map(k=>[k,c[k]]),old.recognition,true));
  const details=el("details"); details.append(el("summary",c.optional)); const naturals=el("div",undefined,"naturalness");
  for(const field of ["prompt","first","second"]) {
    const label=el("label",c[field]), select=el("select"); select.name=`naturalness_${field}`;
    for(const value of ["","good","awkward","unclear"]) { const o=el("option",value?c[value]:c.unrated); o.value=value; select.append(o); }
    select.value=old.naturalness?.[field]||""; label.append(select); naturals.append(label);
  }
  details.append(naturals); form.append(details);
  const noteLabel=el("label",c.note,"field"), note=el("textarea"); note.name="note"; note.maxLength=4000; note.rows=3; note.value=old.note||""; noteLabel.append(note); form.append(noteLabel);
  const nav=el("div",undefined,"toolbar bottom"), prev=button(c.previous,()=>move("item",position-1)); prev.dataset.prev="true"; prev.disabled=position===0;
  const save=el("button",position===packet.total_items-1?c.saveLast:c.save,"primary"); save.type="submit";
  nav.append(prev,button(c.skip,()=>move(position===packet.total_items-1?"review":"item",Math.min(position+1,packet.total_items-1))),save); form.append(nav);
  form.addEventListener("input",markDirty);
  form.addEventListener("submit",async e=>{
    e.preventDefault(); const fd=new FormData(form);
    if(!fd.get("choice")) { say(c.required,true); return; }
    const naturalness={}; for(const field of ["prompt","first","second"]) if(fd.get(`naturalness_${field}`)) naturalness[field]=fd.get(`naturalness_${field}`);
    await submit("/api/response",{item_id:data.id,response:{choice:fd.get("choice"),recognition:fd.get("recognition")||null,note:fd.get("note"),naturalness}},()=>{
      if(position===packet.total_items-1) view="review"; else position++;
      render(); say(c.saved); window.scrollTo(0,0);
    });
  }); app.append(form);
}
function review() {
  const c=t(), missing=packet.total_items-Object.keys(state.responses).length;
  const declined=Object.values(state.responses).filter(x=>x.choice==="abstain").length;
  app.append(el("h1",c.summary),el("p",c.progress(Object.keys(state.responses).length,packet.total_items)),el("p",c.breakdown(packet.total_items-missing-declined,declined,missing)),el("p",c.summaryGuide));
  const list=el("ol",undefined,"review-list"); packet.items.forEach((data,i)=>{ const row=el("li"); row.append(button(String(i+1),()=>move("item",i),state.responses[data.id]?"saved":"")); list.append(row); }); app.append(list);
  const form=el("form"); if(missing) {
    form.append(el("p",c.remaining(missing)));
    const label=el("label",c.reason,"field"), textarea=el("textarea"); textarea.name="remaining_reason"; textarea.maxLength=4000; label.append(textarea); form.append(label);
  }
  const label=el("label",undefined,"check-line"), input=el("input"); input.type="checkbox"; input.name="confirm"; label.append(input,el("span",c.lockCheck)); form.append(label);
  const nav=el("div",undefined,"toolbar bottom"), finish=el("button",c.finalize,"primary"); finish.type="submit"; nav.append(button(c.back,()=>move("item",firstUnanswered())),finish); form.append(nav);
  form.addEventListener("input",()=>{dirty=true;});
  form.addEventListener("submit",async e=>{
    e.preventDefault(); const fd=new FormData(form), reason=String(fd.get("remaining_reason")||"").trim();
    if(!fd.get("confirm")||(missing&&!reason)) { say(c.finalizeMissing,true); return; }
    await submit("/api/finalize",{confirm:true,remaining_reason:reason},()=>{view="locked";render();clearNotice();window.scrollTo(0,0);});
  }); app.append(form);
}
function render() {
  document.documentElement.lang=language; document.querySelector("#site-title").textContent=t().title;
  document.querySelector("#language").textContent=language==="ja"?"English":"日本語";
  document.querySelector("#footer").textContent=t().footer;
  app.replaceChildren(); app.setAttribute("aria-busy","false");
  if(state.locked) { app.append(el("h1",t().locked),el("p",t().progress(Object.keys(state.responses).length,packet.total_items)),el("p",t().lockedText),downloadLink()); return; }
  if(view==="intro") intro();
  else if(view==="ready") { app.append(el("h1",t().welcome),el("p",t().guide),button(t().start,()=>submit("/api/start",{},()=>{view="item";position=firstUnanswered();render();clearNotice();}),"primary")); }
  else if(view==="review") review(); else item();
}
document.querySelector("#language").addEventListener("click",()=>{if(!canLeave()||pendingRequest)return;dirty=false;language=language==="ja"?"en":"ja";clearNotice();render();});
window.addEventListener("beforeunload",e=>{if(dirty||pendingRequest){e.preventDefault();e.returnValue="";}});
(async()=>{
  try { [packet,state]=await Promise.all([readJSON("/api/packet"),readJSON("/api/state")]); render(); }
  catch(_){ app.setAttribute("aria-busy","false"); app.replaceChildren(el("h1",t().loadFail)); }
})();
