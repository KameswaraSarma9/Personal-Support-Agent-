"""
Generates data/sso_configuration_guide.pdf — the required PDF document
in the knowledge base, covering Single Sign-On (SSO) setup and troubleshooting.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

doc = SimpleDocTemplate(
    "data/sso_configuration_guide.pdf",
    pagesize=letter,
    topMargin=0.75 * inch,
    bottomMargin=0.75 * inch,
    leftMargin=0.85 * inch,
    rightMargin=0.85 * inch,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, spaceAfter=14)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15, spaceAfter=6)
bullet_style = ParagraphStyle("Bullet", parent=body, leftIndent=14)

story = []

story.append(Paragraph("Single Sign-On (SSO) Configuration Guide", title_style))
story.append(Paragraph(
    "This document explains how to configure SAML-based Single Sign-On for an organization "
    "account, and how to resolve the most common SSO login failures.",
    body
))

story.append(Paragraph("1. Supported SSO Providers", h2))
story.append(Paragraph(
    "SSO is available on Pro and Enterprise plans and supports any SAML 2.0 compliant Identity "
    "Provider (IdP). Commonly used providers include Okta, Azure Active Directory, Google "
    "Workspace, and OneLogin. OAuth-only providers without SAML support are not currently supported.",
    body
))

story.append(Paragraph("2. Initial Setup Steps", h2))
story.append(ListFlowable([
    ListItem(Paragraph("Go to Org Settings &gt; Security &gt; Single Sign-On and click \"Configure SSO.\"", bullet_style)),
    ListItem(Paragraph("Download the generated Service Provider (SP) metadata XML file.", bullet_style)),
    ListItem(Paragraph("Upload this metadata file into your Identity Provider's application configuration.", bullet_style)),
    ListItem(Paragraph("Your IdP will generate an Identity Provider metadata XML or a metadata URL — paste this into the corresponding field in our dashboard.", bullet_style)),
    ListItem(Paragraph("Map the required attributes: email (required), first_name, last_name, and optionally department for auto-provisioning rules.", bullet_style)),
    ListItem(Paragraph("Click \"Test Connection\" before enabling SSO enforcement organization-wide.", bullet_style)),
], bulletType="bullet"))

story.append(Paragraph("3. Enforcing SSO Org-Wide", h2))
story.append(Paragraph(
    "Once tested successfully, enabling \"Enforce SSO\" will require all members to authenticate "
    "via the configured IdP and will disable standard email/password login for the organization. "
    "The Owner account retains a break-glass password login option for emergency access, accessible "
    "only via a separate recovery link sent to the Owner's recovery email on file.",
    body
))

story.append(Paragraph("4. Common Error: \"SAML Response Invalid\"", h2))
story.append(Paragraph(
    "This error usually indicates a mismatch between the certificate registered in our system and "
    "the one currently used by the IdP to sign responses. IdPs periodically rotate signing certificates.",
    body
))
story.append(Paragraph("Resolution steps:", body))
story.append(ListFlowable([
    ListItem(Paragraph("Re-download the current signing certificate from your IdP.", bullet_style)),
    ListItem(Paragraph("Upload it under Org Settings &gt; Security &gt; Single Sign-On &gt; Certificate.", bullet_style)),
    ListItem(Paragraph("Confirm the certificate has not expired by checking its validity dates.", bullet_style)),
], bulletType="bullet"))

story.append(Paragraph("5. Common Error: \"Attribute Mapping Failed — Missing Email\"", h2))
story.append(Paragraph(
    "This occurs when the IdP does not send the email attribute in the expected SAML assertion "
    "field. Confirm the attribute statement in the IdP configuration uses the exact name configured "
    "on our side (default expected name is \"email\", case-sensitive). Some IdPs default to sending "
    "\"mail\" or \"emailAddress\" instead, which must be explicitly remapped.",
    body
))

story.append(Paragraph("6. Just-In-Time (JIT) Provisioning", h2))
story.append(Paragraph(
    "When enabled, JIT provisioning automatically creates a new user account on first successful "
    "SSO login, assigning the default role configured in Org Settings. If JIT provisioning is "
    "disabled, users must be manually invited before they can log in via SSO, even if their IdP "
    "authentication succeeds.",
    body
))

story.append(Paragraph("7. Users Locked Out After Enabling SSO", h2))
story.append(Paragraph(
    "If a user cannot log in after SSO enforcement is enabled, the most common cause is that their "
    "account was not provisioned (JIT disabled and no manual invite sent), or their IdP-side account "
    "is disabled/unlicensed for this application. Confirm provisioning status under Org Settings &gt; "
    "Members before assuming a technical fault.",
    body
))

story.append(Paragraph("8. When to Escalate", h2))
story.append(Paragraph(
    "The following SSO scenarios require escalation to a human agent, as they involve organization-wide "
    "access risk:",
    body
))
story.append(ListFlowable([
    ListItem(Paragraph("An organization is fully locked out of SSO login with no working break-glass access.", bullet_style)),
    ListItem(Paragraph("A request to disable SSO enforcement urgently due to an IdP outage.", bullet_style)),
    ListItem(Paragraph("Suspected certificate or metadata tampering by an unauthorized party.", bullet_style)),
    ListItem(Paragraph("Any request to bypass SAML validation as a \"temporary\" workaround.", bullet_style)),
], bulletType="bullet"))

doc.build(story)
print("PDF generated.")
