(function () {
"use strict";
const dialog=document.getElementById("plurk-help-dialog");
if (!dialog || typeof dialog.showModal!=="function") return;
let opener=null, position=[0,0];
dialog.addEventListener("keydown",event=>{
 if(event.key!=="Tab") return;
 const controls=Array.from(dialog.querySelectorAll('a[href],button:not([disabled]),[tabindex="0"]')).filter(e=>e.getClientRects().length);
 const first=controls[0],last=controls[controls.length-1];
 if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
 else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
});
const titles={guide:"使用說明",privacy:"隱私權說明"};
function show(kind,trigger){
 if(!dialog.open){opener=trigger;position=[window.scrollX,window.scrollY];}
 dialog.dataset.content=kind;
 document.getElementById("plurk-help-title").textContent=titles[kind];
 const onAddPage=trigger.closest('#新增表符');
 dialog.querySelector('.publisher-dialog-foot button').textContent=onAddPage?'關閉，回到新增':'關閉，回到搜尋';
 dialog.querySelectorAll("[data-dialog-content]").forEach(section=>section.hidden=section.dataset.dialogContent!==kind);
 dialog.querySelector(".publisher-dialog-body").scrollTop=0;
 if(!dialog.open){document.documentElement.classList.add("plurk-dialog-open");dialog.showModal();}
 dialog.querySelector("[data-dialog-close]").focus({preventScroll:true});
}
dialog.addEventListener("close",()=>{
 document.documentElement.classList.remove("plurk-dialog-open");
 if(opener && opener.isConnected) opener.focus({preventScroll:true});
 window.scrollTo(position[0],position[1]);
});
document.addEventListener("click",event=>{
 const close=event.target.closest("[data-dialog-close]");
 if(close && dialog.contains(close)){dialog.close();return;}
 const link=event.target.closest("a");
 if(!link || event.button!==0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || link.target==="_blank") return;
 if(dialog.contains(link) && link.hasAttribute("data-author-link")){
  event.preventDefault();dialog.close();
  const author=document.getElementById("button_bar_about_author");
  if(author) author.click(); else window.location.href=link.href;
  return;
 }
 const url=new URL(link.href,location.href);
 if(url.origin!==location.origin){if(dialog.contains(link)){link.target="_blank";link.rel="noopener noreferrer";}return;}
 const kind=link.id==="search_help_trigger"?"guide":url.pathname.replace(/\/$/,"")==="/guide"?"guide":url.pathname.replace(/\/$/,"")==="/privacy"?"privacy":null;
 if(kind){event.preventDefault();show(kind,link);}
});
})();
