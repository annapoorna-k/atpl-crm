/* global Office */
let context;
const status = document.getElementById("status");
const form = document.getElementById("link-form");
const pursuitSelect = document.getElementById("pursuit");
const contactBox = document.getElementById("contacts");

function setStatus(message, error = false) {
  status.textContent = message;
  status.className = error ? "status error" : "status";
}
async function json(path, options = {}) {
  const response = await fetch(`/api/v1/${path}`, { credentials: "include", ...options });
  const value = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(value.detail || "Open ATPLCRM in this browser and sign in, then retry.");
  return value;
}
function selectedItem() {
  const item = Office.context.mailbox.item;
  const current = Office.context.mailbox.userProfile.emailAddress.toLowerCase();
  const from = item.from?.emailAddress || item.sender?.emailAddress || "";
  const collect = (list) => (list || []).map((person) => person.emailAddress).filter(Boolean);
  const participants = [...new Set([from, ...collect(item.to), ...collect(item.cc)].filter(Boolean))];
  return {
    item,
    subject: item.subject || "Outlook email",
    reference: item.itemId,
    date: item.dateTimeCreated || new Date(),
    direction: from.toLowerCase() === current ? "Outbound" : "Inbound",
    participants,
  };
}
function attachmentBlob(item, attachment) {
  return new Promise((resolve, reject) => item.getAttachmentContentAsync(attachment.id, (result) => {
    if (result.status !== Office.AsyncResultStatus.Succeeded) return reject(new Error(`Could not read ${attachment.name}.`));
    if (result.value.format !== Office.MailboxEnums.AttachmentContentFormat.Base64) return resolve(null);
    const binary = atob(result.value.content); const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    resolve(new File([bytes], attachment.name, { type: attachment.contentType || "application/octet-stream" }));
  }));
}
async function initialize() {
  try {
    context = await json("bootstrap/");
    const pursuits = [...context.opportunities, ...context.leads.filter((lead) => lead.outcome !== "Converted")].filter((row) => row.can_work);
    pursuitSelect.innerHTML = pursuits.map((row) => `<option value="${row.id}" data-company="${row.company_id}">${row.company} · ${row.name}</option>`).join("");
    if (!pursuits.length) throw new Error("You do not have an editable pursuit to link this message to.");
    renderContacts(); pursuitSelect.addEventListener("change", renderContacts);
    const selected = selectedItem();
    setStatus(`${selected.direction} · ${selected.subject} · ${(selected.item.attachments || []).length} attachment(s)`);
    form.hidden = false;
  } catch (error) { setStatus(error.message, true); }
}
function renderContacts() {
  const company = pursuitSelect.selectedOptions[0]?.dataset.company;
  contactBox.innerHTML = context.contacts.filter((person) => person.company_id === company).map((person) => `<label><input type="checkbox" name="recipient" value="${person.id}" />${person.name} · ${person.email}</label>`).join("") || "No contacts are registered for this company.";
}
form.addEventListener("submit", async (event) => {
  event.preventDefault(); const button = document.getElementById("submit"); button.disabled = true;
  try {
    const selected = selectedItem(); const body = new FormData();
    body.set("pursuit", pursuitSelect.value); body.set("subject", selected.subject); body.set("message_reference", selected.reference);
    body.set("email_date", new Date(selected.date).toISOString()); body.set("direction", selected.direction);
    body.set("participants", JSON.stringify(selected.participants)); body.set("classification", document.getElementById("classification").value);
    body.set("internal_only", document.getElementById("internal").checked ? "true" : "false");
    body.set("recipient_contact_ids", JSON.stringify([...document.querySelectorAll('input[name="recipient"]:checked')].map((input) => input.value)));
    for (const attachment of selected.item.attachments || []) { const file = await attachmentBlob(selected.item, attachment); if (file) body.append("attachments", file); }
    const session = await json("session/");
    await json("artifacts/emails/", { method: "POST", headers: { "X-CSRFToken": session.csrf }, body });
    setStatus("Linked to ATPLCRM. Email metadata and supported file attachments are now registered."); form.hidden = true;
  } catch (error) { setStatus(error.message, true); }
  finally { button.disabled = false; }
});

Office.onReady((info) => { if (info.host === Office.HostType.Outlook) void initialize(); else setStatus("Open this task pane from Outlook.", true); });
