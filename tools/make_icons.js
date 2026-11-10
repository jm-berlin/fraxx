// Erzeugt die App-Icons (PNG) aus icons/phraxx.svg. Aufruf im Repo-Ordner: node tools/make_icons.js
const {chromium}=require('playwright');const fs=require('fs');
const svg=fs.readFileSync('icons/phraxx.svg','utf8');
const inner=svg.replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'');
const glyph=inner.replace(/<rect[^>]*\/>/,'');
function page(size,mode){ // mode: round (transparent corners), square (full bg), mask (full bg, glyph scaled to 0.8)
 let body;
 if(mode==='round') body=svg;
 else if(mode==='square') body=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="#161314"/>${glyph}</svg>`;
 else body=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="#161314"/><g transform="translate(256 256) scale(.8) translate(-256 -256)">${glyph}</g></svg>`;
 return `<html><body style="margin:0;background:transparent">${body.replace('<svg ',`<svg width="${size}" height="${size}" `)}</body></html>`;}
(async()=>{const b=await chromium.launch();
for(const [f,s,m] of [['icon-192.png',192,'round'],['icon-512.png',512,'round'],['favicon-32.png',32,'round'],['apple-touch-icon.png',180,'square'],['maskable-512.png',512,'mask']]){
 const p=await b.newPage({viewport:{width:s,height:s}});await p.setContent(page(s,m));
 await p.screenshot({path:'icons/'+f,omitBackground:true,clip:{x:0,y:0,width:s,height:s}});await p.close();}
await b.close()})();
