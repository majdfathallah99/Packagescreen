/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted, onPatched } from "@odoo/owl";
function forceFullscreen(){const d=document.querySelector(".o_dialog.modal .modal-dialog");const c=document.querySelector(".o_dialog.modal .modal-content");if(d){d.style.maxWidth="100%";d.style.width="100vw";d.style.height="100vh";d.style.margin="0"}if(c){c.style.height="100vh";c.style.borderRadius="0";c.style.border="0"}}
function focusBarcode(root){const el=root?.querySelector('input[name="barcode"]');if(el){el.focus();el.select?.();}}
patch(FormController.prototype,"pc_kiosk_fullscreen",{setup(){this._super(...arguments);onMounted(()=>{setTimeout(()=>{forceFullscreen();focusBarcode(this.root?.el);},0)});onPatched(()=>{setTimeout(()=>{forceFullscreen();focusBarcode(this.root?.el);},0)});},async saveButtonClicked(ev){ev?.preventDefault?.();},});
document.addEventListener("keydown",(ev)=>{const a=document.activeElement;if(a&&a.getAttribute("name")==="barcode"&&ev.key==="Enter"){ev.preventDefault();ev.stopPropagation();a.dispatchEvent(new Event("change",{bubbles:true}));a.blur();setTimeout(()=>a.focus(),60);}});