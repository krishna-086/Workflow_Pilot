# Sample data for WorkflowPilot demo scenarios

# 1. SAMPLE_EMPLOYEE (onboarding scenario)
SAMPLE_EMPLOYEE = {
    "name": "Priya Sharma",
    "email": "priya.sharma@company.com",
    "department": "Engineering",
    "role": "Senior Frontend Developer",
    "manager": "Rahul Mehta",
    "start_date": "2026-03-30"
}

# 2. SAMPLE_TRANSCRIPT (meeting scenario)
SAMPLE_TRANSCRIPT = """[Rahul Mehta]: Alright everyone, thanks for joining. So, umm, we're here to discuss the new dashboard feature launch. I think we're getting close, but there's still a few things we need to nail down before we can ship this thing. Ananya, do you want to kick us off with the product side?

[Ananya Desai]: Yeah, absolutely. So the dashboard is looking really good from what I've seen. We've got strong interest from our beta customers, and I think this could be a big win for Q2. But we need to move fast — our competitors are launching similar features, so timing is critical here.

[Vikram Patel]: Right, right. On the design side, I've got the main flows done, but there's a few edge cases we're still working through. I need, like, maybe another two days to finalize everything? I can have the final mockups ready by Friday if that works.

[Rahul Mehta]: Friday works. Let's lock that in — Vikram, you'll get us those final mockups by end of week.

[Vikram Patel]: Yep, committed.

[Neha Gupta]: Okay, from QA perspective, um, I'm a bit concerned about test coverage. We've done manual testing but we really need automated regression tests for this dashboard. It's got a lot of moving parts. I can set that up, but I'll need maybe a week to get the full suite in place.

[Rahul Mehta]: That's fine. Neha, go ahead and prioritize setting up those automated tests. Better to be thorough than rush it.

[Ananya Desai]: Agreed. Quality is super important here. Oh, and speaking of documentation — we're going to need API documentation for the dashboard endpoints, right? Like, before we hand this off to customers?

[Rahul Mehta]: Oh yeah, that's... yeah, we definitely need that. Umm... who's going to own that?

[Vikram Patel]: I mean, I can help with the structure, but I'm not really the right person to write the technical docs.

[Neha Gupta]: Yeah, I'm already pretty slammed with the test automation...

[Ananya Desai]: Right, okay. Well, we need someone to handle it. Let's... figure that out offline, I guess?

[Rahul Mehta]: Yeah, we'll sort it out. Let's keep moving.

[Ananya Desai]: Cool. So on my end, I need to schedule user testing sessions with our beta customers. I'm thinking we run those next week, get feedback, and then iterate before the public launch. I'll coordinate with the customer success team and get those scheduled.

[Rahul Mehta]: Perfect. That sounds good.

[Vikram Patel]: Oh, one more thing — are we using feature flags for this rollout? Like, can we do a gradual release?

[Rahul Mehta]: Umm, we should, yeah. Feature flags would be smart. I think our deployment pipeline supports that, but we might need to update a few things. Let me... I'll look into that.

[Ananya Desai]: Okay, so you're going to handle the feature flag setup?

[Rahul Mehta]: Well, I mean, I'll check on it. We might need DevOps to help, but yeah, I'll make sure it gets done.

[Neha Gupta]: Sounds good. Anything else we need to cover?

[Rahul Mehta]: I think that's everything for today. Let's, uh, let's reconvene next week once Vikram's mockups are ready and we can do a final review. Thanks everyone!"""

# 3. SAMPLE_PARTICIPANTS (meeting scenario)
SAMPLE_PARTICIPANTS = ["Rahul Mehta", "Ananya Desai", "Vikram Patel", "Neha Gupta"]

# 4. SAMPLE_APPROVAL (SLA scenario)
SAMPLE_APPROVAL = {
    "request_id": "PROC-2026-0847",
    "type": "procurement",
    "requested_by": "Amit Verma",
    "approver": "David Kim",
    "submitted_at": "2026-03-27T09:00:00Z",
    "sla_deadline": "2026-03-29T09:00:00Z"
}

# 5. ALL_DEMO_DATA (convenience dict)
ALL_DEMO_DATA = {
    "onboarding": {
        "employee": SAMPLE_EMPLOYEE
    },
    "meeting": {
        "transcript": SAMPLE_TRANSCRIPT,
        "participants": SAMPLE_PARTICIPANTS
    },
    "sla": {
        "approval": SAMPLE_APPROVAL
    }
}
