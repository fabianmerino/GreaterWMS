(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([[58],{"15c3":function(t,e,o){"use strict";var n=o("c4db"),a=o.n(n);e["default"]=a.a},"6d4e":function(t,e,o){"use strict";o.r(e);var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",[o("transition",{attrs:{appear:"","enter-active-class":"animated fadeIn"}},[o("q-table",{staticClass:"my-sticky-header-column-table shadow-24",attrs:{data:t.table_list,"row-key":"id",separator:t.separator,loading:t.loading,columns:t.columns,"hide-bottom":"",pagination:t.pagination,"no-data-label":"No data","no-results-label":"No data you want","table-style":{height:t.height},flat:"",bordered:""},on:{"update:pagination":function(e){t.pagination=e}},scopedSlots:t._u([{key:"top",fn:function(){return[o("q-btn-group",{attrs:{push:""}},[o("q-btn",{attrs:{label:t.$t("stock.view_stocklist.cyclecount"),icon:"refresh"},on:{click:function(e){return t.getList()}}},[o("q-tooltip",{attrs:{"content-class":"bg-amber text-black shadow-4",offset:[10,10],"content-style":"font-size: 12px"}},[t._v(t._s(t.$t("stock.view_stocklist.cyclecounttip")))])],1),o("q-btn",{attrs:{label:t.$t("stock.view_stocklist.downloadcyclecount"),icon:"cloud_download"},on:{click:function(e){return t.downloadData()}}},[o("q-tooltip",{attrs:{"content-class":"bg-amber text-black shadow-4",offset:[10,10],"content-style":"font-size: 12px"}},[t._v("\n              "+t._s(t.$t("stock.view_stocklist.downloadcyclecounttip"))+"\n            ")])],1)],1),o("q-space"),o("q-btn-group",{attrs:{push:""}},[o("q-btn",{attrs:{color:"purple",label:t.$t("stock.view_stocklist.cyclecountresult")},on:{click:function(e){return t.ConfirmCounts()}}},[o("q-tooltip",{attrs:{"content-class":"bg-amber text-black shadow-4",offset:[10,10],"content-style":"font-size: 12px"}},[t._v("\n              "+t._s(t.$t("stock.view_stocklist.cyclecountresulttip"))+"\n            ")])],1)],1)]},proxy:!0},{key:"body",fn:function(e){return[o("q-tr",{attrs:{props:e}},[o("q-td",{key:"bin_name",attrs:{props:e}},[t._v(t._s(e.row.bin_name))]),o("q-td",{key:"goods_code",attrs:{props:e}},[t._v(t._s(e.row.goods_code))]),o("q-td",{key:"goods_qty",attrs:{props:e}},[t._v(t._s(e.row.goods_qty))]),o("q-td",{key:"physical_inventory",attrs:{props:e}},[o("q-input",{attrs:{dense:"",outlined:"",square:"",type:"number",label:t.$t("stock.view_stocklist.physical_inventory"),rules:[function(e){return e&&e>0||0==e||t.error1}]},on:{blur:function(o){return t.blurHandler(e.row.physical_inventory)}},model:{value:e.row.physical_inventory,callback:function(o){t.$set(e.row,"physical_inventory",t._n(o))},expression:"props.row.physical_inventory"}})],1),o("q-td",{key:"difference",attrs:{props:e}},[t._v(t._s(e.row.physical_inventory-e.row.goods_qty))]),o("q-td",{key:"action",staticStyle:{width:"50px"},attrs:{props:e}},[o("q-btn",{directives:[{name:"show",rawName:"v-show",value:"Inbound"!==t.$q.localStorage.getItem("staff_type")&&"Outbound"!==t.$q.localStorage.getItem("staff_type"),expression:"$q.localStorage.getItem('staff_type') !== 'Inbound' && $q.localStorage.getItem('staff_type') !== 'Outbound'"}],attrs:{round:"",flat:"",push:"",color:"purple",icon:"repeat"},on:{click:function(t){e.row.physical_inventory=0}}},[o("q-tooltip",{attrs:{"content-class":"bg-amber text-black shadow-4",offset:[10,10],"content-style":"font-size: 12px"}},[t._v("\n                "+t._s(t.$t("stock.view_stocklist.recyclecounttip"))+"\n              ")])],1)],1)],1)]}}])})],1),[o("div",{staticClass:"q-pa-lg flex flex-center"},[o("q-btn",{attrs:{flat:"",push:"",color:"dark",label:t.$t("no_data")}})],1)],o("q-dialog",{model:{value:t.CountFrom,callback:function(e){t.CountFrom=e},expression:"CountFrom"}},[o("q-card",{staticClass:"shadow-24"},[o("q-bar",{staticClass:"bg-light-blue-10 text-white rounded-borders",staticStyle:{height:"50px"}},[o("div",[t._v(t._s(t.$t("confirminventoryresults")))]),o("q-space"),o("q-btn",{directives:[{name:"close-popup",rawName:"v-close-popup"}],attrs:{dense:"",flat:"",icon:"close"}},[o("q-tooltip",{attrs:{"content-class":"bg-amber text-black shadow-4"}},[t._v(t._s(t.$t("index.close")))])],1)],1),o("q-card-section",{staticClass:"scroll",staticStyle:{"max-height":"325px",width:"400px"}},[t._v(t._s(t.$t("deletetip")))]),o("div",{staticStyle:{float:"right",padding:"15px 15px 15px 0"}},[o("q-btn",{staticStyle:{"margin-right":"25px"},attrs:{color:"white","text-color":"black"},on:{click:function(e){return t.preloadDataCancel()}}},[t._v(t._s(t.$t("cancel")))]),o("q-btn",{attrs:{color:"primary"},on:{click:function(e){return t.ConfirmCount()}}},[t._v(t._s(t.$t("submit")))])],1)],1)],1)],2)},a=[],s=(o("5319"),o("bd4c")),i=o("a357"),c=o("18d6"),l=o("3004"),r={name:"cyclyecount",data(){return{openid:"",login_name:"",authin:"0",pathname:"cyclecount/",separator:"cell",loading:!1,height:"",table_list:[],bin_size_list:[],bin_property_list:[],warehouse_list:[],columns:[{name:"bin_name",required:!0,label:this.$t("warehouse.view_binset.bin_name"),align:"left",field:"bin_name"},{name:"goods_code",label:this.$t("stock.view_stocklist.goods_code"),field:"goods_code",align:"center"},{name:"goods_qty",label:this.$t("stock.view_stocklist.on_hand_inventory"),field:"goods_qty",align:"center"},{name:"physical_inventory",label:this.$t("stock.view_stocklist.physical_inventory"),field:"physical_inventory",align:"center"},{name:"difference",label:this.$t("stock.view_stocklist.difference"),field:"difference",align:"center"},{name:"action",label:this.$t("action"),align:"right"}],pagination:{page:1,rowsPerPage:"10000"},options:[],error1:this.$t("stock.view_stocklist.error1"),CountFrom:!1}},methods:{getList(){var t=this;Object(l["e"])(t.pathname,{}).then((e=>{t.table_list=e})).catch((e=>{t.$q.notify({message:e.detail,icon:"close",color:"negative"})}))},reFresh(){var t=this;t.getList()},ConfirmCount(){var t=this;t.table_list.length?Object(l["h"])(t.pathname,t.table_list).then((e=>{t.CountFrom=!1,t.$q.notify({message:"Success Confirm Cycle Count",icon:"check",color:"green"}),t.reFresh()})).catch((e=>{t.$q.notify({message:e.detail,icon:"close",color:"negative"})})):(t.CountFrom=!1,t.$q.notify({message:t.$t("notice.cyclecounterror"),icon:"close",color:"negative"}))},preloadDataCancel(){var t=this;t.CountFrom=!1},downloadData(){var t=this;c["a"].has("auth")?Object(l["f"])("cyclecount/filecyclecountday/?lang="+c["a"].getItem("lang")).then((e=>{var o=Date.now(),n=s["b"].formatDate(o,"YYYYMMDDHHmmssSSS");const a=Object(i["a"])("cyclecountday_"+n+".csv","\ufeff"+e.data,"text/csv");!0!==a&&t.$q.notify({message:"Browser denied file download...",color:"negative",icon:"warning"})})):t.$q.notify({message:t.$t("notice.loginerror"),color:"negative",icon:"warning"})},ConfirmCounts(){var t=this;t.CountFrom=!0},blurHandler(t){t=t.toString().replace(/^(0+)|[^\d]+/g,"")}},created(){var t=this;c["a"].has("openid")?t.openid=c["a"].getItem("openid"):(t.openid="",c["a"].set("openid","")),c["a"].has("login_name")?t.login_name=c["a"].getItem("login_name"):(t.login_name="",c["a"].set("login_name","")),c["a"].has("auth")?(t.authin="1",t.getList()):t.authin="0"},mounted(){var t=this;t.$q.platform.is.electron?t.height=String(t.$q.screen.height-290)+"px":t.height=t.$q.screen.height-290+"px"},updated(){},destroyed(){}},d=r,p=o("42e1"),u=o("15c3"),h=o("eaac"),_=o("e7a9"),g=o("9c40"),f=o("05c0"),b=o("2c91"),y=o("bd08"),m=o("db86"),v=o("27f9"),w=o("24e8"),k=o("f09f"),q=o("d847"),$=o("a370"),x=o("7f67"),C=o("eebe"),S=o.n(C),Q=Object(p["a"])(d,n,a,!1,null,null,null);"function"===typeof u["default"]&&Object(u["default"])(Q);e["default"]=Q.exports;S()(Q,"components",{QTable:h["a"],QBtnGroup:_["a"],QBtn:g["a"],QTooltip:f["a"],QSpace:b["a"],QTr:y["a"],QTd:m["a"],QInput:v["a"],QDialog:w["a"],QCard:k["a"],QBar:q["a"],QCardSection:$["a"]}),S()(Q,"directives",{ClosePopup:x["a"]})},c4db:function(t,e){}}]);