"use strict";
const $ = s => document.querySelector(s);
const esc = v => String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let lang="ja", packet, state, index=0, view="setup", busy=false, pending=null;
const drafts={};
const COPY={
 ja:{title:"手がかりと判断",intro:"問いを分けて、読む",purpose:"改訂版の試用です。正解を当てる試験ではありません。24の場面で、指定された問いだけについて判断してください。問題文は英語のまま表示します。",
 distinction:"まず、その問いへの答えを決められるかを選びます。決められる場合だけ、問いへのYes／Noを選んでください。判断を保留するときは、Yes／Noを推測で埋める必要はありません。",
 example:"たとえば「会議を提案した」という文から「会議が既に行われたと分かるか？」への答えはNoと決められます。一方、文の意味が分からず問いへの答えも決まらない場合は、判断を保留できます。",
 known:"今回は著者による開発試用です。過去の結果や照合に接した履歴は保持し、独立した評価として扱いません。想定回答・モデル結果は表示しません。",
 english:"英語の問題文を読むことへの慣れ",research:"この研究自体を知っていますか",model:"この研究のモデル結果を見ましたか",comparison:"以前の回答と想定・モデルの照合を見ましたか",
 choose:"選んでください",comfortable:"無理なく読める",sometimes_difficult:"ときどき難しい",difficult:"難しい",prefer_not_to_say:"回答しない",yes:"はい",no:"いいえ",unsure:"覚えていない／分からない",
 start:"試用を始める",scene:"場面",saved:"保存済み",of:"／",question:"問い",assess:"この問いへの答えを決められますか？",decide_yes:"はい — 答えを決められる",decide_no:"いいえ — 判断を保留する",answer:"上の英語の問いへの答え",held:"判断保留として保存します。命題へのNoには変換しません。",
 quality:"問題文・問いの英語は理解しやすいですか（任意）",recognition:"この場面への見覚え（任意）",reasons:"判断に影響した点（任意・複数可）",cue_meaning:"手がかりの意味",report_reliability:"報告を信頼できるか",missing_context:"追加の文脈が必要",wording:"言葉の分かりにくさ",other:"その他",note:"メモ（任意）",abstain:"この場面への回答を控える",save:"保存して次へ",save_last:"保存して見直す",back:"前の場面",review:"保存状況を見直す",review_title:"保存状況と確定",unanswered:"未保存",edited:"未保存の変更あり",remaining:"未保存の場面を残す理由（残す場合は必須）",confirm:"このまとまりを確定し、回答を変更できなくすることを確認しました。",finalize:"回答を確定する",locked:"回答を確定しました",locked_text:"ありがとうございました。回答はこの端末内に保存されています。想定回答やモデルとの比較は自動では開きません。",download:"保存した回答をダウンロード",footer:"この端末内だけで保存します。判断保留・未記入・回答を控えることを区別します。",complete_fields:"各問いについて、答えを決められるかと、必要なYes／Noを選んでください。",setup_fields:"開始前の4項目を選んでください。",save_ok:"保存しました。",retry:"同じ保存要求を再送",network:"保存を確認できませんでした。再送するか、再読み込みして保存済みの状態を確認してください。",unsaved:"未保存の変更があります。確定前に、その場面を保存してください。",finalize_check:"確定の確認と、必要なら未保存の理由を記入してください。"},
 en:{title:"Cues and judgments",intro:"Separate the questions",purpose:"This is a revised development tryout, not a test of correct answers. Read 24 scenes and judge only the specified questions. Stimuli remain in English.",
 distinction:"First decide whether you can settle the question. Only if you can, answer the proposition Yes or No. If you cannot decide, you do not need to guess.",
 example:"For example, ‘a meeting was proposed’ allows a No answer to ‘does this establish that the meeting already happened?’ If you cannot understand the message or settle the question, you may leave the judgment undecided.",
 known:"This is an author development tryout. Known exposure to prior results and comparisons is retained; these judgments are not independent validation. No intended answers or model results are displayed.",
 english:"Comfort reading the English stimuli",research:"Have you encountered this research before?",model:"Have you seen model results from this research?",comparison:"Have you seen comparisons of your earlier responses with intended answers or model results?",
 choose:"Please select",comfortable:"Comfortable",sometimes_difficult:"Sometimes difficult",difficult:"Difficult",prefer_not_to_say:"Prefer not to say",yes:"Yes",no:"No",unsure:"Unsure / do not remember",
 start:"Start the tryout",scene:"Scene",saved:"saved",of:" / ",question:"Question",assess:"Can you decide the answer to this question?",decide_yes:"Yes — I can decide",decide_no:"No — leave undecided",answer:"Answer to the English question above",held:"Saved as undecided, never converted to a No answer to the proposition.",
 quality:"Is the English scene/question easy to understand? (optional)",recognition:"Do you recognize this scene? (optional)",reasons:"Factors affecting your judgment (optional; select any)",cue_meaning:"Meaning of the cue",report_reliability:"Reliability of the report",missing_context:"Additional context needed",wording:"Unclear wording",other:"Other",note:"Note (optional)",abstain:"Abstain from this scene",save:"Save and continue",save_last:"Save and review",back:"Previous scene",review:"Review saved responses",review_title:"Review and finalize",unanswered:"not saved",edited:"unsaved changes",remaining:"Reason for leaving scenes unanswered (required if any remain)",confirm:"I confirm that finalizing will lock this batch against further edits.",finalize:"Finalize responses",locked:"Responses finalized",locked_text:"Thank you. Responses are saved on this device. Intended answers and model comparisons are not revealed automatically.",download:"Download saved responses",footer:"Saved on this device only. Undecided, missing, and abstained responses remain distinct.",complete_fields:"For every question, choose whether you can decide and, where needed, Yes or No.",setup_fields:"Complete all four setup questions.",save_ok:"Saved.",retry:"Retry the same save request",network:"Save could not be confirmed. Retry, or reload to inspect the saved state.",unsaved:"Unsaved edits remain. Save those scenes before finalizing.",finalize_check:"Confirm finalization and explain any remaining unanswered scenes."}
};
const t=()=>COPY[lang];
function notice(message,error=false){$("#notice").textContent=message;$("#notice").className=error?"error":"";}
function options(values,selected){return `<option value="">${esc(t().choose)}</option>`+values.map(v=>`<option value="${v}"${selected===v?' selected':''}>${esc(t()[v])}</option>`).join("");}
function select(name,label,values,selected){return `<label class="field">${esc(label)}<select name="${name}">${options(values,selected)}</select></label>`;}
function radios(name,legend,values,current){return `<fieldset><legend>${esc(legend)}</legend><div class="choices">${values.map(([value,label])=>`<label class="choice"><input type="radio" name="${name}" value="${value}"${current===value?' checked':''}><span>${esc(label)}</span></label>`).join("")}</div></fieldset>`;}
function emptyResponse(){return {judgments:{},abstain:false,language_clear:null,recognition:null,reasons:[],note:""};}
function cleanSaved(value){if(!value)return emptyResponse();const {saved_at_utc,...rest}=value;return structuredClone(rest);}
function currentDraft(){const item=packet.items[index];return drafts[item.id]||cleanSaved(state.responses[item.id]);}
function capture(){
 const form=$("#response-form");if(!form)return;
 const data=new FormData(form),value=emptyResponse();value.abstain=data.has("abstain");
 if(!value.abstain)for(const q of packet.items[index].questions){
  const d=data.get(q.id+"_decide"),a=data.get(q.id+"_answer");
  if(d!==null)value.judgments[q.id]={decidable:d==="yes",answer:d==="yes"?(a===null?null:a==="yes"):null};
 }
 value.language_clear=data.get("language_clear")===""?null:data.get("language_clear")==="yes";
 value.recognition=data.get("recognition")||null;value.reasons=data.getAll("reason");value.note=data.get("note")||"";
 drafts[packet.items[index].id]=value;
}
function stable(value){if(Array.isArray(value))return value.map(stable);if(value&&typeof value==="object")return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value;}
function dirtyIds(){return Object.keys(drafts).filter(id=>JSON.stringify(stable(drafts[id]))!==JSON.stringify(stable(cleanSaved(state.responses[id]))));}
function render(){
 document.documentElement.lang=lang;$("#site-title").textContent=t().title;$("#language").textContent=lang==="ja"?"English":"日本語";$("#footer").textContent=t().footer;
 const app=$("#app");app.setAttribute("aria-busy","false");
 if(state.locked){app.innerHTML=`<h1>${esc(t().locked)}</h1><p>${esc(t().locked_text)}</p><a class="download" href="/api/export" download>${esc(t().download)}</a>`;return;}
 if(!state.started){
  const s=state.setup||{};
  app.innerHTML=`<h1>${esc(t().intro)}</h1><p>${esc(t().purpose)}</p><p>${esc(t().distinction)}</p><p>${esc(t().example)}</p><p class="muted">${esc(t().known)}</p><form id="setup-form">${select("english_confidence",t().english,["comfortable","sometimes_difficult","difficult","prefer_not_to_say"],s.english_confidence)}${["research","model","comparison"].map(k=>select(k+"_exposure",t()[k],["yes","no","unsure","prefer_not_to_say"],s[k+"_exposure"])).join("")}<div class="toolbar"><button class="primary" type="submit">${esc(t().start)}</button></div></form>`;
  $("#setup-form").onsubmit=async event=>{event.preventDefault();const setup=Object.fromEntries(new FormData(event.target));if(Object.values(setup).some(v=>!v)){notice(t().setup_fields,true);return;}await mutate("setup",{setup},async()=>{await mutate("start",{},()=>{view="item";render();});});};return;
 }
 if(view==="review"){
  const saved=Object.keys(state.responses).length,dirty=dirtyIds();
  app.innerHTML=`<h1>${esc(t().review_title)}</h1><p>${saved}${t().of}${packet.total_items} ${esc(t().saved)}</p><ul class="review">${packet.items.map((x,i)=>`<li><button data-item="${i}" class="${state.responses[x.id]?'saved':''}" title="${esc(dirty.includes(x.id)?t().edited:(state.responses[x.id]?t().saved:t().unanswered))}">${i+1}${dirty.includes(x.id)?'*':''}</button></li>`).join("")}</ul><form id="finalize-form"><label class="field">${esc(t().remaining)}<textarea name="remaining_reason" maxlength="4000"></textarea></label><label class="check-line"><input type="checkbox" name="confirm"><span>${esc(t().confirm)}</span></label><div class="toolbar"><button class="primary" type="submit">${esc(t().finalize)}</button><a class="download" href="/api/export" download>${esc(t().download)}</a></div></form>`;
  app.querySelectorAll("[data-item]").forEach(b=>b.onclick=()=>{index=Number(b.dataset.item);view="item";render();window.scrollTo(0,0);});
  $("#finalize-form").onsubmit=async e=>{e.preventDefault();if(dirtyIds().length){notice(t().unsaved,true);return;}const data=new FormData(e.target),reason=data.get("remaining_reason");if(!data.has("confirm")||(saved<packet.total_items&&!reason.trim())){notice(t().finalize_check,true);return;}await mutate("finalize",{confirm:true,remaining_reason:reason},render);};return;
 }
 const item=packet.items[index],draft=currentDraft();
 app.innerHTML=`<p class="progress">${esc(t().scene)} ${index+1}${t().of}${packet.total_items} · ${Object.keys(state.responses).length} ${esc(t().saved)}</p><h1>${esc(t().scene)} ${index+1}</h1><p class="prompt" lang="en">${esc(item.prompt)}</p><form id="response-form"><div id="questions"${draft.abstain?' hidden':''}>${item.questions.map((q,i)=>{
  const j=draft.judgments[q.id];return `<section class="question"><p class="progress">${esc(t().question)} ${i+1}</p><h2 lang="en">${esc(q.text)}</h2>${radios(q.id+"_decide",t().assess,[["yes",t().decide_yes],["no",t().decide_no]],j?(j.decidable?'yes':'no'):null)}<div data-answer="${q.id}"${!j?.decidable?' hidden':''}>${radios(q.id+"_answer",t().answer,[["yes","Yes"],["no","No"]],j?.answer===true?'yes':j?.answer===false?'no':null)}</div><small data-held="${q.id}"${!j||j.decidable?' hidden':''}>${esc(t().held)}</small></section>`;
 }).join("")}</div><label class="check-line"><input name="abstain" type="checkbox"${draft.abstain?' checked':''}><span>${esc(t().abstain)}</span></label>${select("language_clear",t().quality,["yes","no"],draft.language_clear===null?null:draft.language_clear?'yes':'no')}${select("recognition",t().recognition,["yes","no","unsure"],draft.recognition)}<fieldset><legend>${esc(t().reasons)}</legend><div class="reasons">${["cue_meaning","report_reliability","missing_context","wording","other"].map(v=>`<label><input type="checkbox" name="reason" value="${v}"${draft.reasons.includes(v)?' checked':''}><span>${esc(t()[v])}</span></label>`).join("")}</div></fieldset><label class="field">${esc(t().note)}<textarea name="note" maxlength="4000">${esc(draft.note)}</textarea></label><div class="toolbar"><button type="submit" class="primary">${esc(index+1<packet.total_items?t().save:t().save_last)}</button><button type="button" id="review">${esc(t().review)}</button>${index>0?`<button type="button" id="back">${esc(t().back)}</button>`:''}</div></form>`;
 const form=$("#response-form");
 form.onchange=e=>{if(e.target.name.endsWith("_decide")){const id=e.target.name.replace("_decide","");app.querySelector(`[data-answer="${id}"]`).hidden=e.target.value!=="yes";app.querySelector(`[data-held="${id}"]`).hidden=e.target.value!=="no";if(e.target.value==="no")form.querySelectorAll(`[name="${id}_answer"]`).forEach(x=>x.checked=false);}if(e.target.name==="abstain")$("#questions").hidden=e.target.checked;capture();};form.oninput=capture;
 form.onsubmit=async e=>{e.preventDefault();capture();const response=drafts[item.id];if(!response.abstain&&item.questions.some(q=>!response.judgments[q.id]||(response.judgments[q.id].decidable&&response.judgments[q.id].answer===null))){notice(t().complete_fields,true);return;}await mutate("response",{item_id:item.id,response},()=>{delete drafts[item.id];if(index+1<packet.total_items)index++;else view="review";render();notice(t().save_ok);window.scrollTo(0,0);});};
 $("#review").onclick=()=>{capture();view="review";render();window.scrollTo(0,0);};if($("#back"))$("#back").onclick=()=>{capture();index--;render();window.scrollTo(0,0);};
}
function setBusy(value){busy=value;document.querySelectorAll("button").forEach(b=>b.disabled=value);}
async function sendPending(){
 if(busy||!pending)return;setBusy(true);const job=pending;
 try{
  const response=await fetch("/api/"+job.action,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(job.body)});
  const value=await response.json();
  if(!response.ok){pending=null;if(value.state)state=value.state;throw new Error(value.message||"Save rejected");}
  state=value;pending=null;setBusy(false);notice("");await job.done();
 }catch(error){notice(error.message+" "+t().network,true);if(pending){const button=document.createElement("button");button.textContent=t().retry;button.onclick=sendPending;$("#notice").append(button);}}
 finally{setBusy(false);}
}
async function mutate(action,fields,done){if(busy||pending)return;pending={action,body:{request_id:crypto.randomUUID(),revision:state.revision,instruction_language:lang,...fields},done};await sendPending();}
$("#language").onclick=()=>{capture();if(!state.started){const form=$("#setup-form");if(form)state.setup=Object.fromEntries(new FormData(form));}lang=lang==="ja"?"en":"ja";render();};
window.addEventListener("beforeunload",event=>{if(state&&!state.locked&&(dirtyIds().length||pending)){event.preventDefault();event.returnValue="";}});
Promise.all([fetch("/api/packet").then(r=>{if(!r.ok)throw new Error("Packet unavailable");return r.json();}),fetch("/api/state").then(r=>{if(!r.ok)throw new Error("State unavailable");return r.json();})]).then(([p,s])=>{packet=p;state=s;index=Math.max(0,packet.items.findIndex(x=>!state.responses[x.id]));view=state.started?"item":"setup";render();}).catch(e=>{notice(e.message,true);$("#app").setAttribute("aria-busy","false");});
