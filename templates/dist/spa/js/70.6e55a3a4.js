(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([[70],{1242:function(e,t,a){"use strict";a.r(t);var i=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",{staticStyle:{width:"100%",height:"100%","margin-top":"-40px"}},[a("line-chart")],1)},o=[],s=function(){var e=this,t=e.$createElement,a=e._self._c||t;return a("div",[a("q-card",{staticClass:"shadow-24"},[a("q-card-section",{staticClass:"text-h6"},[e._v("\n      第三周入库报表\n    ")]),a("q-card-section",[a("div",{ref:"linechart",style:{height:e.height},attrs:{id:"lineChart"}})]),a("q-resize-observer",{on:{resize:e.onResize}})],1)],1)},r=[],n=(a("3004"),{name:"LineChart",data(){return{height:"",model:!1,pathname:"LineChart/",options:{color:["#80FFA5","#00DDFF","#37A2FF","#FF0087","#FFBF00"],tooltip:{trigger:"axis",axisPointer:{type:"cross",label:{backgroundColor:"#6a7985"}}},legend:{data:["Line 1","Line 2","Line 3","Line 4","Line 5"],bottom:10},grid:{left:"3%",right:"4%",bottom:"20%",top:"5%",containLabel:!0},xAxis:[{type:"category",boundaryGap:!1,data:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]}],yAxis:[{type:"value"}],series:[{name:"Line 1",type:"line",stack:"Total",smooth:!0,lineStyle:{width:0},showSymbol:!1,areaStyle:{opacity:.8,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"rgba(128, 255, 165)"},{offset:1,color:"rgba(1, 191, 236)"}])},emphasis:{focus:"series"},data:[140,232,101,264,90,340,250]},{name:"Line 2",type:"line",stack:"Total",smooth:!0,lineStyle:{width:0},showSymbol:!1,areaStyle:{opacity:.8,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"rgba(0, 221, 255)"},{offset:1,color:"rgba(77, 119, 255)"}])},emphasis:{focus:"series"},data:[120,282,111,234,220,340,310]},{name:"Line 3",type:"line",stack:"Total",smooth:!0,lineStyle:{width:0},showSymbol:!1,areaStyle:{opacity:.8,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"rgba(55, 162, 255)"},{offset:1,color:"rgba(116, 21, 219)"}])},emphasis:{focus:"series"},data:[320,132,201,334,190,130,220]},{name:"Line 4",type:"line",stack:"Total",smooth:!0,lineStyle:{width:0},showSymbol:!1,areaStyle:{opacity:.8,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"rgba(255, 0, 135)"},{offset:1,color:"rgba(135, 0, 157)"}])},emphasis:{focus:"series"},data:[220,402,231,134,190,230,120]},{name:"Line 5",type:"line",stack:"Total",smooth:!0,lineStyle:{width:0},showSymbol:!1,label:{show:!0,position:"top"},areaStyle:{opacity:.8,color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"rgba(255, 191, 0)"},{offset:1,color:"rgba(224, 62, 76)"}])},emphasis:{focus:"series"},data:[220,302,181,234,210,290,150]}]},line_chart:null}},mounted(){this.init();var e=this;e.$q.platform.is.electron?e.height=String(e.$q.screen.height-290)+"px":e.height=e.$q.screen.height-290+"px"},watch:{"$q.dark.isActive":function(){this.init()}},methods:{getdata(){},init(){const e=document.getElementById("lineChart");echarts.dispose(e);const t=this.model?"dark":"light";this.line_chart=echarts.init(e,t),this.line_chart.setOption(this.options)},onResize(){this.line_chart&&this.line_chart.resize()}}}),l=n,c=a("42e1"),h=a("f09f"),d=a("a370"),p=a("3980"),y=a("eebe"),f=a.n(y),m=Object(c["a"])(l,s,r,!1,null,"1ab0b173",null),g=m.exports;f()(m,"components",{QCard:h["a"],QCardSection:d["a"],QResizeObserver:p["a"]});var b={name:"V1",components:{LineChart:g}},u=b,w=Object(c["a"])(u,i,o,!1,null,null,null);t["default"]=w.exports}}]);