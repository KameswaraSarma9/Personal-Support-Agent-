# Team Management and Permissions

## Overview
This article explains roles, permissions, and common issues when managing team members.

## Role Types
- **Owner**: Full access, including billing and account deletion. Exactly one Owner per account; ownership can be transferred but not duplicated.
- **Admin**: Full access except billing and account deletion.
- **Member**: Can create and edit projects but cannot manage team members or settings.
- **Viewer**: Read-only access across all projects.

## Inviting Team Members
1. Go to **Team Settings > Invite Member**.
2. Enter their email and select a role.
3. An invite email is sent with a link valid for 7 days.
4. If not accepted within 7 days, the invite expires and must be resent.

## Common Issue: Invite Email Not Received
- Confirm the email was typed correctly — invites cannot be resent to a corrected email, a new invite must be created instead.
- Check spam/promotions folders.
- Corporate email firewalls sometimes block automated invite emails; suggest the invitee whitelist our sending domain.

## Transferring Ownership
Ownership transfer requires the current Owner to initiate the transfer from **Team Settings > Transfer Ownership**, and the new Owner must accept via a confirmation email. This cannot be done by an Admin on the Owner's behalf, even with the Owner's permission communicated verbally — it must be initiated by the Owner's own account for security reasons.

## Removing a Team Member
Removing a member immediately revokes their access. Any projects solely owned by that member (not shared) become inaccessible until reassigned by an Admin or Owner under **Team Settings > Orphaned Projects**.

## Permission Errors ("You don't have access to this resource")
This usually means the user's role does not include the required permission, or they were removed from a specific project's shared access list even though they remain on the team. Check **Project Settings > Access** to confirm.

## When to Escalate
Escalate when: an Owner has lost access to their account and needs ownership manually reassigned, when ownership transfer is contested between team members, or when permission errors persist despite correct role assignment.
