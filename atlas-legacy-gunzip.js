(function(){
  "use strict";
  window.__atlasLegacyGunzip=function(gz){
    var pos=0,bitbuf=0,bitcnt=0,out=[];
    function need(n){if(pos+n>gz.length)throw new Error("Truncated gzip data");}
    need(10);
    if(gz[0]!==31||gz[1]!==139||gz[2]!==8)throw new Error("Unsupported gzip stream");
    var flags=gz[3];pos=10;
    if(flags&4){need(2);var xlen=gz[pos]|(gz[pos+1]<<8);pos+=2;need(xlen);pos+=xlen;}
    if(flags&8){while(pos<gz.length&&gz[pos++]!==0){}}
    if(flags&16){while(pos<gz.length&&gz[pos++]!==0){}}
    if(flags&2){need(2);pos+=2;}
    function bits(n){
      while(bitcnt<n){if(pos>=gz.length-8)throw new Error("Truncated deflate stream");bitbuf|=gz[pos++]<<bitcnt;bitcnt+=8;}
      var v=bitbuf&((1<<n)-1);bitbuf>>>=n;bitcnt-=n;return v;
    }
    function rev(v,n){var r=0;while(n--){r=(r<<1)|(v&1);v>>>=1;}return r;}
    function tree(lengths){
      var max=0,i;for(i=0;i<lengths.length;i++)if(lengths[i]>max)max=lengths[i];
      var count=new Array(max+1),next=new Array(max+1),tab=new Array(max+1),code=0;
      for(i=0;i<=max;i++){count[i]=0;tab[i]={};}
      for(i=0;i<lengths.length;i++)if(lengths[i])count[lengths[i]]++;
      for(i=1;i<=max;i++){code=(code+(count[i-1]||0))<<1;next[i]=code;}
      for(i=0;i<lengths.length;i++)if(lengths[i]){var l=lengths[i],c=rev(next[l]++,l);tab[l][c]=i;}
      return {tab:tab,max:max};
    }
    function sym(t){
      var c=0;
      for(var l=1;l<=t.max;l++){
        c|=bits(1)<<(l-1);
        if(Object.prototype.hasOwnProperty.call(t.tab[l],c))return t.tab[l][c];
      }
      throw new Error("Invalid Huffman code");
    }
    function fixed(){
      var ll=new Array(288),dd=new Array(32),i;
      for(i=0;i<=143;i++)ll[i]=8;for(;i<=255;i++)ll[i]=9;for(;i<=279;i++)ll[i]=7;for(;i<=287;i++)ll[i]=8;
      for(i=0;i<32;i++)dd[i]=5;
      return [tree(ll),tree(dd)];
    }
    var lb=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
    var le=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
    var db=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
    var de=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
    var order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
    var done=false;
    while(!done){
      done=bits(1)!==0;var type=bits(2),lt,dt;
      if(type===0){
        bitbuf=0;bitcnt=0;need(4);
        var len=gz[pos]|(gz[pos+1]<<8),nlen=gz[pos+2]|(gz[pos+3]<<8);pos+=4;
        if(((len^65535)&65535)!==nlen)throw new Error("Bad stored block");
        need(len);for(var j=0;j<len;j++)out.push(gz[pos++]);continue;
      }
      if(type===1){var f=fixed();lt=f[0];dt=f[1];}
      else if(type===2){
        var hlit=bits(5)+257,hdist=bits(5)+1,hclen=bits(4)+4,cl=new Array(19),i;
        for(i=0;i<19;i++)cl[i]=0;
        for(i=0;i<hclen;i++)cl[order[i]]=bits(3);
        var ct=tree(cl),lens=[],total=hlit+hdist;
        while(lens.length<total){
          var s=sym(ct);
          if(s<=15)lens.push(s);
          else if(s===16){
            if(!lens.length)throw new Error("Bad repeat code");
            var r=bits(2)+3,v=lens[lens.length-1];while(r--&&lens.length<total)lens.push(v);
          }else if(s===17){var r0=bits(3)+3;while(r0--&&lens.length<total)lens.push(0);}
          else if(s===18){var r1=bits(7)+11;while(r1--&&lens.length<total)lens.push(0);}
          else throw new Error("Bad code-length symbol");
        }
        lt=tree(lens.slice(0,hlit));dt=tree(lens.slice(hlit));
      }else throw new Error("Reserved deflate block type");
      while(true){
        var s2=sym(lt);
        if(s2<256){out.push(s2);continue;}
        if(s2===256)break;
        if(s2<257||s2>285)throw new Error("Bad length symbol");
        var li=s2-257,len2=lb[li]+(le[li]?bits(le[li]):0),ds=sym(dt);
        if(ds>29)throw new Error("Bad distance symbol");
        var dist=db[ds]+(de[ds]?bits(de[ds]):0);
        if(dist>out.length)throw new Error("Invalid deflate distance");
        var start=out.length-dist;
        for(var k=0;k<len2;k++)out.push(out[start+k]);
      }
    }
    function utf8(a){
      var res=[],chunk="",i=0,c,c2,c3,c4,cp;
      function flush(){if(chunk){res.push(chunk);chunk="";}}
      while(i<a.length){
        c=a[i++];
        if(c<128)cp=c;
        else if(c<224){c2=a[i++];cp=((c&31)<<6)|(c2&63);}
        else if(c<240){c2=a[i++];c3=a[i++];cp=((c&15)<<12)|((c2&63)<<6)|(c3&63);}
        else{
          c2=a[i++];c3=a[i++];c4=a[i++];cp=((c&7)<<18)|((c2&63)<<12)|((c3&63)<<6)|(c4&63);cp-=65536;
          chunk+=String.fromCharCode(55296+(cp>>10),56320+(cp&1023));if(chunk.length>8192)flush();continue;
        }
        chunk+=String.fromCharCode(cp);if(chunk.length>8192)flush();
      }
      flush();return res.join("");
    }
    return utf8(out);
  };
})();
