// Drives ui/index.html in headless Chrome via DevTools protocol; records assertions + screenshots.
const {spawn}=require('child_process'),fs=require('fs');
const dir=__dirname;const out=[];
const chrome=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-gpu','--remote-debugging-port=9333','--window-size=760,620','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let tabs;for(let i=0;i<40;i++){try{tabs=await (await fetch('http://127.0.0.1:9333/json')).json();if(tabs.length)break}catch(e){}await sleep(250)}
 const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let id=0;const pend={};ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}};
 const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
 const ev=async e=>(await send('Runtime.evaluate',{expression:e,returnByValue:true})).result.result.value;
 const shot=async n=>{const r=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(dir+'/evidence/'+n,Buffer.from(r.result.data,'base64'))};
 const check=(n,ok,d)=>{out.push((ok?'PASS ':'FAIL ')+n+(d?' ('+d+')':''));};
 await send('Page.enable');await send('Page.navigate',{url:'file://'+dir+'/ui/index.html'});await sleep(800);
 const count=()=>ev('document.querySelectorAll("#list li").length');
 check('initial render shows 5 seed tasks',await count()===5,'count='+await count());
 check('sorted: first shown is a high-priority task',await ev('document.querySelector("#list li .p").textContent')==='high');
 await shot('ui_1_initial.png');
 await ev('document.getElementById("add").click()');
 check('empty title rejected with message',(await ev('document.getElementById("err").textContent'))==='Title is required'&&await count()===5);
 await ev('document.getElementById("title").value="Ship the demo";document.getElementById("prio").value="high";document.getElementById("due").value="2026-11-24";document.getElementById("add").click()');
 check('add task -> 6 shown',await count()===6,await ev('document.getElementById("count").textContent'));
 await ev('document.querySelector("#list li .chk").click()');
 check('toggle done updates done count',(await ev('document.getElementById("count").textContent')).includes('2 done'),await ev('document.getElementById("count").textContent'));
 await ev('const f=document.getElementById("fs");f.value="open";f.dispatchEvent(new Event("change"))');
 check('filter open -> 4 shown',await count()===4);
 await shot('ui_2_after_add_toggle_filter.png');
 await ev('document.querySelector("#list li .del").click()');
 check('delete removes one -> 3 shown, 5 total',await count()===3&&(await ev('document.getElementById("count").textContent')).includes('/ 5 total'),await ev('document.getElementById("count").textContent'));
 await shot('ui_3_after_delete.png');
 fs.writeFileSync(dir+'/evidence/ui_interaction_results.txt',out.join('\n')+'\n');console.log(out.join('\n'));
 const failed=out.filter(l=>l.startsWith('FAIL')).length;console.log(failed?failed+' FAILED':'ALL PASSED');
 ws.close();chrome.kill();process.exit(failed?1:0);
})().catch(e=>{console.log('ERR',e);chrome.kill();process.exit(1)});
