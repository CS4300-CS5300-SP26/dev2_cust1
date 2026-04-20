/**
 * The River — Live Social Activity Feed (Vanilla JS)
 * Ported from Svelte/SpacetimeDB → Django fitness app
 * Fitness-themed events, orange accent colour scheme
 */
(function () {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFIG / CONSTANTS
  // ═══════════════════════════════════════════════════════════════════════════

  const RIVER_TIMING = {
    eventDurationMs: [14000, 32000],
    flowStartDelayMs: 1500,
    generatorIntervalMs: [1500, 3500],
    seedDurationMs: [18000, 30000],
    commentsPerEvent: [2, 7],
    commentMaxAgeMs: 120000,
  };

  const SPEED_MIN = 0.05;
  const SPEED_MAX = 2.0;
  const SPEED_PIPS = 7;
  const RIVER_WIDTH_MIN = 200;
  const RIVER_WIDTH_MAX = 500;
  const DEFAULT_RIVER_WIDTH = 350;

  const LANES = [0.15, 0.55, 0.30, 0.72, 0.22, 0.62, 0.42, 0.78, 0.18, 0.68, 0.35, 0.50, 0.82, 0.25, 0.65, 0.45];
  const LANE_MIN = 0.15;
  const LANE_MAX = 0.85;

  // ── Fitness-themed event types ──
  const EVENT_COLORS = {
    workout_complete:    '#e85c00',
    personal_record:     '#e85c00',
    fitness_achievement: '#e85c00',
    gear_purchase:       '#999999',
    workout_review:      '#cccccc',
    team_milestone:      '#e85c00',
    challenge_complete:  '#e85c00',
    fitness_event:       '#e85c00',
  };

  const EVENT_ICONS = {
    workout_complete:    '💪',
    personal_record:     '🏆',
    fitness_achievement: '🎖️',
    gear_purchase:       '🛒',
    workout_review:      '⭐',
    team_milestone:      '🤝',
    challenge_complete:  '🔥',
    fitness_event:       '✨',
  };

  const EVENT_WEIGHTS = {
    workout_complete: 30,
    personal_record: 10,
    fitness_achievement: 8,
    gear_purchase: 15,
    workout_review: 12,
    team_milestone: 8,
    challenge_complete: 15,
    fitness_event: 2,
  };

  const CAL_POOL = [120, 200, 350, 500, 650, 800, 1200];

  // ── Rarity system ──
  const RARITY_LABELS = {
    common: 'Common', uncommon: 'Uncommon', rare: 'Rare',
    epic: 'Epic', legendary: 'Legendary', mythic: 'Mythic',
  };

  const EVENT_LIFETIME = {
    common:    5 * 60 * 1000,
    uncommon:  15 * 60 * 1000,
    rare:      60 * 60 * 1000,
    epic:      4 * 60 * 60 * 1000,
    legendary: 24 * 60 * 60 * 1000,
    mythic:    72 * 60 * 60 * 1000,
  };

  // ── Tier colours — unified with accent palette ──
  const TIER_COLORS = {
    bronze:   '#e85c00',
    silver:   '#e85c00',
    gold:     '#e85c00',
    platinum: '#e85c00',
    diamond:  '#e85c00',
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════════════════

  let nextId = 1;
  let activeEvents = [];
  let expiredEvents = [];
  let riverSpeed = loadSaved('spotter-river-speed', SPEED_MIN, function (v) {
    var f = parseFloat(v);
    return !isNaN(f) && f >= SPEED_MIN && f <= SPEED_MAX ? Math.round(f * 10) / 10 : null;
  });
  let riverCollapsed = false;
  let riverWidth = loadSaved('spotter-river-width', DEFAULT_RIVER_WIDTH, function (v) {
    var n = parseInt(v, 10);
    return !isNaN(n) && n >= RIVER_WIDTH_MIN && n <= RIVER_WIDTH_MAX ? n : null;
  });

  let hoveredId = null;
  let expandUp = false;
  let cardX = 0;
  let commentsExpandedId = null;
  let nowMs = Date.now();
  let riverHeight = 700;
  let generatorTimeout = null;

  // Hold tracking (hover-pause)
  const holdAccum = new Map();
  let currentHoldId = null;
  let currentHoldStart = 0;

  // DOM refs
  let sidebarEl = null;
  let channelEl = null;
  let mobileFieldEl = null;
  let mobilePopupEl = null;

  // ═══════════════════════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════════════════════

  function loadSaved(key, fallback, parse) {
    try {
      var v = localStorage.getItem(key);
      if (v != null) { var r = parse(v); if (r != null) return r; }
    } catch (e) { /* noop */ }
    return fallback;
  }
  function savePref(key, val) { try { localStorage.setItem(key, String(val)); } catch (e) { /* noop */ } }

  function pickRarity(eventType) {
    if (eventType === 'fitness_event') return 'mythic';
    var roll = Math.random() * 10000;
    if (roll < 8000) return 'common';
    if (roll < 9000) return 'uncommon';
    if (roll < 9500) return 'rare';
    if (roll < 9600) return 'epic';
    if (roll < 9610) return 'legendary';
    if (roll < 9611) return 'mythic';
    return 'common';
  }

  function pickClassInteractive(rarity) {
    if (rarity === 'common' || rarity === 'uncommon') return false;
    return Math.random() < 0.1;
  }

  function getHoldTime(eventId, t) {
    var total = holdAccum.get(eventId) || 0;
    if (currentHoldId === eventId && currentHoldStart > 0) total += t - currentHoldStart;
    return total;
  }

  function getDriftMultiplier() {
    return 2.0 - ((riverSpeed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)) * 1.8;
  }

  function getProgress(ev, t) {
    var startMs = ev.createdAt + ev.animDelay;
    var elapsed = t - startMs - getHoldTime(ev.id, t);
    return elapsed / (ev.flowDurationMs * getDriftMultiplier());
  }

  function timeAgo(ms) {
    var sec = Math.max(0, Math.floor((nowMs - ms) / 1000));
    if (sec < 5) return 'just now';
    if (sec < 60) return sec + 's ago';
    var min = Math.floor(sec / 60);
    if (min < 60) return min + 'm ago';
    var hr = Math.floor(min / 60);
    if (hr < 24) return hr + 'h ago';
    return Math.floor(hr / 24) + 'd ago';
  }

  function formatRemaining(ms) {
    if (ms <= 0) return 'Expired';
    var s = Math.ceil(ms / 1000);
    if (s < 60) return s + 's';
    var m = Math.floor(s / 60), rs = s % 60;
    if (m < 60) return m + 'm ' + rs + 's';
    var h = Math.floor(m / 60), rm = m % 60;
    if (h < 24) return h + 'h ' + rm + 'm';
    return Math.floor(h / 24) + 'd ' + (h % 24) + 'h';
  }

  function lifetimeColor(pct) {
    if (pct > 60) return '#e85c00';
    if (pct > 30) return '#e85c00';
    if (pct > 10) return '#D42338';
    return '#D42338';
  }

  // ── Pill helpers ──
  function rarityBg(ev) {
    return '#181818';
  }

  function rarityBorder(ev) {
    if (ev.rarity === 'mythic') return 'rgba(232,92,0,0.4)';
    if (ev.rarity === 'legendary') return 'rgba(232,92,0,0.3)';
    if (ev.rarity === 'epic') return 'rgba(232,92,0,0.2)';
    if (ev.rarity === 'rare') return 'rgba(232,92,0,0.15)';
    if (ev.rarity === 'uncommon') return 'rgba(232,92,0,0.1)';
    return '#242424';
  }

  function isHighlight(ev) { return ev.eventType === 'personal_record' || ev.eventType === 'fitness_achievement'; }
  function isSpecial(ev) { return ev.eventType === 'fitness_event'; }

  function pillSize(ev) {
    if (ev.eventType === 'fitness_event') return 'lg';
    if (ev.eventType === 'personal_record' || ev.eventType === 'fitness_achievement' || ev.eventType === 'team_milestone') return 'md';
    return 'sm';
  }

  function pillLabel(ev) {
    if (isSpecial(ev)) return ev.title;
    return ev.title.replace(ev.actorUsername + ' ', '');
  }

  function eventTypeLabel(ev) {
    var m = {
      workout_complete: 'Workout', personal_record: 'PR', fitness_achievement: 'Achievement',
      gear_purchase: 'Gear', workout_review: 'Review', team_milestone: 'Team',
      challenge_complete: 'Challenge', fitness_event: 'Event',
    };
    return m[ev.eventType] || ev.eventType;
  }

  function pillBadge(ev) {
    switch (ev.eventType) {
      case 'workout_complete': { var m = ev.title.match(/(\d+)\s*cal/i); return m ? m[1] + 'cal' : ''; }
      case 'personal_record': return 'PR';
      case 'challenge_complete': return '✓';
      case 'workout_review': { var s = (ev.title.match(/★/g) || []).length; return s ? '★'.repeat(Math.min(s, 3)) : ''; }
      default: return '';
    }
  }

  function tierColor(tier) { return '#e85c00'; }

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  // ═══════════════════════════════════════════════════════════════════════════
  // MOCK DATA — Fitness themed
  // ═══════════════════════════════════════════════════════════════════════════

  const MOCK_USERS = [
    { username: 'IronMike',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=IronMike',    tier: 'gold' },
    { username: 'RunnerKay',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=RunnerKay',   tier: 'platinum' },
    { username: 'YogaLuna',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=YogaLuna',    tier: 'silver' },
    { username: 'BeastMode',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=BeastMode',   tier: 'diamond' },
    { username: 'SweatQueen',  avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=SweatQueen',  tier: 'gold' },
    { username: 'GymRat42',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=GymRat42',    tier: 'bronze' },
    { username: 'FlexFiona',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=FlexFiona',   tier: 'silver' },
    { username: 'LiftKing',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=LiftKing',    tier: 'gold' },
    { username: 'CardioSam',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=CardioSam',   tier: 'platinum' },
    { username: 'StretchPat',  avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=StretchPat',  tier: 'bronze' },
    { username: 'PlankMaster', avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=PlankMaster', tier: 'silver' },
    { username: 'GainsGuru',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=GainsGuru',   tier: 'diamond' },
  ];

  const COMMENT_USERS = [
    { username: 'FitFam99',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=FitFam99',    tier: 'silver' },
    { username: 'GymBro',      avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=GymBro',      tier: 'diamond' },
    { username: 'YogaVibes',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=YogaVibes',   tier: 'bronze' },
    { username: 'LiftLife',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=LiftLife',     tier: 'platinum' },
    { username: 'RunClub',     avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=RunClub',     tier: 'bronze' },
    { username: 'MealPrep',    avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=MealPrep',    tier: 'silver' },
    { username: 'SwoleMate',   avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=SwoleMate',   tier: 'diamond' },
    { username: 'CoreStrong',  avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=CoreStrong',  tier: 'silver' },
  ];

  const COMMENT_TEMPLATES = [
    'Nice! 🔥', 'Let\'s gooo!', 'Beast mode!', 'Insane effort 😤', 'W',
    'Massive!', 'How?!', 'Goals right there', 'GG!', 'Keep pushing 💪',
    'Sheesh', 'Built different', 'Drop the routine', 'No excuses!',
    'Respect ✊', 'That\'s wild', 'Keep grinding 🏋️', 'Jealous ngl',
    'Big W right there', 'The grind pays off', 'Legend status',
  ];

  // Fitness-themed mock event templates
  const MOCK_TEMPLATES = [
    {
      type: 'workout_complete',
      weight: EVENT_WEIGHTS.workout_complete,
      generate: function (u) {
        var cal = CAL_POOL[Math.floor(Math.random() * CAL_POOL.length)];
        var workouts = ['Morning HIIT', 'Upper body', 'Leg day', '5K run', 'Cycling session', 'Swimming laps', 'CrossFit WOD', 'Yoga flow'];
        var w = workouts[Math.floor(Math.random() * workouts.length)];
        return { title: u.username + ' burned ' + cal + ' cal', detail: w + ' — keep the streak alive!', actionUrl: '' };
      },
    },
    {
      type: 'personal_record',
      weight: EVENT_WEIGHTS.personal_record,
      generate: function (u) {
        var records = [
          'Bench Press 225 lbs', 'Squat 315 lbs', 'Deadlift 405 lbs',
          '5K in 22:30', 'Mile in 6:15', '100 pushups in 4 min',
          '10K steps before 9 AM', 'Plank 5 min', '30-day streak',
        ];
        var r = records[Math.floor(Math.random() * records.length)];
        return { title: u.username + ' set a new PR!', detail: r + ' — crushing it!', actionUrl: '' };
      },
    },
    {
      type: 'fitness_achievement',
      weight: EVENT_WEIGHTS.fitness_achievement,
      generate: function (u) {
        var achievements = ['First 5K', '100 Workouts', 'Iron Will', 'Marathon Finisher', 'Streak Lord', 'Meal Prep Master'];
        var a = achievements[Math.floor(Math.random() * achievements.length)];
        return { title: u.username + ' unlocked "' + a + '"', detail: 'Achievement unlocked! Dedication pays off.', actionUrl: '' };
      },
    },
    {
      type: 'gear_purchase',
      weight: EVENT_WEIGHTS.gear_purchase,
      generate: function (u) {
        var items = ['Whey Protein', 'Resistance Bands', 'Smart Watch', 'Running Shoes', 'Yoga Mat', 'Kettlebell Set', 'Foam Roller'];
        var item = items[Math.floor(Math.random() * items.length)];
        return { title: u.username + ' grabbed ' + item, detail: 'Gear up! Smart investment for the journey.', actionUrl: '' };
      },
    },
    {
      type: 'workout_review',
      weight: EVENT_WEIGHTS.workout_review,
      generate: function (u) {
        var stars = Math.floor(Math.random() * 2) + 4;
        var classes = ['HIIT Blast', 'Power Yoga', 'Spin Class', 'Body Pump', 'Boxing Basics', 'Pilates Core'];
        var c = classes[Math.floor(Math.random() * classes.length)];
        return { title: u.username + ' rated ' + c + ' ' + '★'.repeat(stars), detail: 'Honest feedback helps the community!', actionUrl: '' };
      },
    },
    {
      type: 'team_milestone',
      weight: EVENT_WEIGHTS.team_milestone,
      generate: function (u) {
        var milestones = ['reached 50K team calories', 'completed weekly challenge', 'recruited 3 new members', 'hit 100 collective workouts'];
        var m = milestones[Math.floor(Math.random() * milestones.length)];
        return { title: u.username + '\'s team ' + m, detail: 'The team grows stronger together!', actionUrl: '' };
      },
    },
    {
      type: 'challenge_complete',
      weight: EVENT_WEIGHTS.challenge_complete,
      generate: function (u) {
        var challenges = ['30-Day Plank', 'Couch to 5K', 'No Sugar Week', '10K Steps Daily', 'Protein Goal Streak', 'Morning Warrior'];
        var c = challenges[Math.floor(Math.random() * challenges.length)];
        return { title: u.username + ' completed "' + c + '"', detail: 'Challenge conquered — on to the next one!', actionUrl: '' };
      },
    },
    {
      type: 'fitness_event',
      weight: EVENT_WEIGHTS.fitness_event,
      generate: function () {
        var events = [
          { title: '🏃 Double Cal Weekend is LIVE', detail: 'All calories tracked count 2× until Sunday. Don\'t miss out!' },
          { title: '💪 Community Challenge starts in 30 min', detail: 'First 100 finishers unlock exclusive badges.' },
          { title: '🏋️ Team Wars: Season 2 begins', detail: 'Compete for exclusive team rewards and bragging rights.' },
        ];
        var picked = events[Math.floor(Math.random() * events.length)];
        return { title: picked.title, detail: picked.detail, actionUrl: '' };
      },
    },
  ];

  // ═══════════════════════════════════════════════════════════════════════════
  // EVENT MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════════

  function generateMockComments(count) {
    var comments = [];
    var now = Date.now();
    var used = {};
    for (var i = 0; i < count; i++) {
      var idx;
      do { idx = Math.floor(Math.random() * COMMENT_USERS.length); } while (used[idx] && Object.keys(used).length < COMMENT_USERS.length);
      used[idx] = true;
      var u = COMMENT_USERS[idx];
      comments.push({
        username: u.username,
        avatarUrl: u.avatarUrl,
        tier: u.tier,
        text: COMMENT_TEMPLATES[Math.floor(Math.random() * COMMENT_TEMPLATES.length)],
        timestamp: now - Math.random() * RIVER_TIMING.commentMaxAgeMs,
      });
    }
    return comments.sort(function (a, b) { return a.timestamp - b.timestamp; });
  }

  function pushRiverEvent(opts) {
    var now = Date.now();
    var dur = RIVER_TIMING.eventDurationMs;
    var durationMs = dur[0] + Math.random() * (dur[1] - dur[0]);
    var spawnDelay = opts.spawnAfterMs != null ? opts.spawnAfterMs : Math.random() * RIVER_TIMING.flowStartDelayMs;
    var id = nextId++;
    var rarity = opts.rarity || pickRarity(opts.eventType);
    var classInteractive = opts.classInteractive != null ? opts.classInteractive : pickClassInteractive(rarity);
    var cpe = RIVER_TIMING.commentsPerEvent;
    var commentCount = Math.floor(Math.random() * (cpe[1] - cpe[0])) + cpe[0];
    var baseLane = opts.forceLane != null ? opts.forceLane : Math.max(LANE_MIN, Math.min(LANE_MAX, LANES[id % LANES.length] + (Math.random() * 0.04 - 0.02)));

    activeEvents.push({
      id: id,
      eventType: opts.eventType,
      actorUsername: opts.actorUsername,
      actorAvatarUrl: opts.actorAvatarUrl,
      actorTier: opts.actorTier,
      title: opts.title,
      detail: opts.detail,
      icon: opts.icon || EVENT_ICONS[opts.eventType],
      color: opts.color || EVENT_COLORS[opts.eventType],
      actionUrl: opts.actionUrl || '',
      rarity: rarity,
      classInteractive: classInteractive,
      sparkCount: Math.floor(Math.random() * 12),
      sparkedByMe: false,
      viewedByMe: false,
      comments: opts.comments || generateMockComments(commentCount),
      createdAt: now,
      expiresAt: now + EVENT_LIFETIME[rarity],
      flowStartAt: now + spawnDelay,
      flowDurationMs: durationMs,
      lane: baseLane,
      wobblePhase: Math.random() * 6.28,
      depth: 0.7 + Math.random() * 0.3,
      animDelay: spawnDelay,
      spawnY: opts.spawnY,
    });
    if (activeEvents.length > 80) activeEvents.splice(0, activeEvents.length - 80);
  }

  function markEventSeen(id) {
    var idx = activeEvents.findIndex(function (e) { return e.id === id; });
    if (idx !== -1) {
      activeEvents.splice(idx, 1);
    }
  }

  function sparkEvent(id) {
    var ev = activeEvents.find(function (e) { return e.id === id; });
    if (!ev) return;
    if (ev.sparkedByMe) { ev.sparkedByMe = false; ev.sparkCount = Math.max(0, ev.sparkCount - 1); }
    else { ev.sparkedByMe = true; ev.sparkCount += 1; }
  }

  function addComment(id, text) {
    var ev = activeEvents.find(function (e) { return e.id === id; });
    if (!ev || !text.trim()) return;
    ev.comments.push({
      username: 'You',
      avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=You',
      tier: 'bronze',
      text: text.trim(),
      timestamp: Date.now(),
    });
  }

  function pickWeightedTemplate() {
    var total = MOCK_TEMPLATES.reduce(function (s, t) { return s + t.weight; }, 0);
    var roll = Math.random() * total;
    for (var i = 0; i < MOCK_TEMPLATES.length; i++) {
      roll -= MOCK_TEMPLATES[i].weight;
      if (roll <= 0) return MOCK_TEMPLATES[i];
    }
    return MOCK_TEMPLATES[0];
  }

  function generateMockEvent() {
    var user = MOCK_USERS[Math.floor(Math.random() * MOCK_USERS.length)];
    var template = pickWeightedTemplate();
    var data = template.generate(user);
    pushRiverEvent({
      eventType: template.type,
      actorUsername: user.username,
      actorAvatarUrl: user.avatarUrl,
      actorTier: user.tier,
      title: data.title,
      detail: data.detail,
      icon: EVENT_ICONS[template.type],
      color: EVENT_COLORS[template.type],
      actionUrl: data.actionUrl,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MOCK GENERATOR
  // ═══════════════════════════════════════════════════════════════════════════

  function seedEvents() {
    var now = Date.now();
    var seedCount = 25;
    var speedNorm = (riverSpeed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN);
    var seedDriftMult = 2.0 - speedNorm * 1.8;
    for (var i = 0; i < seedCount; i++) {
      var user = MOCK_USERS[(i * 3 + 1) % MOCK_USERS.length];
      var template = pickWeightedTemplate();
      var data = template.generate(user);
      var sd = RIVER_TIMING.seedDurationMs;
      var durationMs = sd[0] + Math.random() * (sd[1] - sd[0]);
      var progress = (i / seedCount) * 0.92 + (Math.random() * 0.04 - 0.02);
      var elapsed = progress * durationMs * seedDriftMult;
      var id = nextId++;
      var laneIdx = i % LANES.length;
      var rarity = pickRarity(template.type);
      var cpe = RIVER_TIMING.commentsPerEvent;
      var commentCount = Math.floor(Math.random() * (cpe[1] - cpe[0])) + cpe[0];
      var isMySpark = (i === 1);
      var isMyComment = (i === 3 || i === 6);
      var comments = generateMockComments(commentCount);
      if (isMyComment) {
        comments.push({
          username: 'You',
          avatarUrl: 'https://api.dicebear.com/9.x/pixel-art/svg?seed=You',
          tier: 'bronze',
          text: i === 3 ? 'Nice effort! 🔥' : 'GG, keep pushing!',
          timestamp: now - Math.random() * 30000,
        });
      }
      activeEvents.push({
        id: id,
        eventType: template.type,
        actorUsername: user.username,
        actorAvatarUrl: user.avatarUrl,
        actorTier: user.tier,
        title: data.title,
        detail: data.detail,
        icon: EVENT_ICONS[template.type],
        color: EVENT_COLORS[template.type],
        actionUrl: data.actionUrl,
        rarity: rarity,
        classInteractive: pickClassInteractive(rarity),
        sparkCount: Math.floor(Math.random() * 12) + (isMySpark ? 1 : 0),
        sparkedByMe: isMySpark,
        viewedByMe: false,
        comments: comments,
        createdAt: now,
        expiresAt: now + EVENT_LIFETIME[rarity],
        flowStartAt: now - elapsed,
        flowDurationMs: durationMs,
        lane: Math.max(LANE_MIN, Math.min(LANE_MAX, LANES[laneIdx] + (Math.random() * 0.03 - 0.015))),
        wobblePhase: Math.random() * 6.28,
        depth: 0.75 + Math.random() * 0.25,
        animDelay: -elapsed,
      });
    }
  }

  function reseedRiver() {
    activeEvents.length = 0;
    seedEvents();
  }

  function scheduleGeneratorTick() {
    var gi = RIVER_TIMING.generatorIntervalMs;
    var base = gi[0] + Math.random() * (gi[1] - gi[0]);
    var speedNorm = (riverSpeed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN);
    var scale = 2.0 - speedNorm * 1.9;
    generatorTimeout = setTimeout(function () {
      generateMockEvent();
      scheduleGeneratorTick();
    }, base * scale);
  }

  function startMockGenerator() {
    if (generatorTimeout) return;
    seedEvents();
    scheduleGeneratorTick();
  }

  function stopMockGenerator() {
    if (generatorTimeout) { clearTimeout(generatorTimeout); generatorTimeout = null; }
  }

  function setSpeed(speed) {
    riverSpeed = Math.max(SPEED_MIN, Math.min(SPEED_MAX, Math.round(speed * 10) / 10));
    savePref('spotter-river-speed', riverSpeed);
    if (generatorTimeout) { clearTimeout(generatorTimeout); generatorTimeout = null; scheduleGeneratorTick(); }
    renderControls();
  }

  function toggleCollapsed() {
    riverCollapsed = !riverCollapsed;
    updateLayout();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDERING — Build HTML strings
  // ═══════════════════════════════════════════════════════════════════════════

  function buildSidebarHTML() {
    return '' +
      '<div class="river-drag-handle" id="river-drag-handle"></div>' +
      '<div class="river-bg"></div>' +
      '<div class="river-border"></div>' +
      '<div class="river-header" id="river-header"></div>' +
      '<div class="river-depth-fog river-depth-fog-top"></div>' +
      '<div class="river-channel" id="river-channel"></div>' +
      '<div class="river-depth-fog river-depth-fog-bottom"></div>' +
      '<div class="river-ambient">' +
        '<div class="river-ambient-text">' +
          '<span class="river-ambient-icon">〰️</span> live feed' +
        '</div>' +
      '</div>';
  }

  function buildMobileHTML() {
    return '' +
      '<div class="river-mobile-bg"></div>' +
      '<div class="river-border-h"></div>' +
      '<div class="river-mobile-logo">' +
        '<span class="river-logo-icon" style="font-size:14px;">〰️</span>' +
      '</div>' +
      '<div class="river-mobile-field" id="river-mobile-field"></div>' +
      '<div id="river-mobile-popup" style="display:none;"></div>';
  }

  function renderControls() {
    var hdr = document.getElementById('river-header');
    if (!hdr) return;

    if (riverCollapsed) {
      hdr.innerHTML = '' +
        '<button class="river-collapse-btn collapsed" id="river-collapse-btn" title="Expand River">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>' +
        '</button>';
    } else {
      var speedNorm = (riverSpeed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN);
      var activePips = Math.round(speedNorm * (SPEED_PIPS - 1));
      var pipsHtml = '<div class="river-pips" id="river-pips">';
      for (var i = 0; i < SPEED_PIPS; i++) {
        var h = 6 + (i / (SPEED_PIPS - 1)) * 10;
        pipsHtml += '<div class="river-pip' + (i <= activePips ? ' active' : '') + '" data-pip="' + i + '" style="height:' + h + 'px;cursor:pointer;"></div>';
      }
      pipsHtml += '</div>';

      hdr.innerHTML = '' +
        '<div class="river-header-left">' +
          '<div class="river-logo">' +
            '<span class="river-logo-icon" style="font-size:16px;">〰️</span>' +
            '<div class="river-logo-ripple"></div>' +
          '</div>' +
          '<div class="river-title-wrap">' +
            '<span class="river-title">RIVER</span>' +
            '<span class="river-subtitle">live feed</span>' +
          '</div>' +
        '</div>' +
        '<div class="river-header-right">' +
          pipsHtml +
          '<button class="river-collapse-btn" id="river-collapse-btn" title="Collapse River">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>' +
          '</button>' +
        '</div>';
    }

    var btn = document.getElementById('river-collapse-btn');
    if (btn) btn.onclick = toggleCollapsed;

    var pipsEl = document.getElementById('river-pips');
    if (pipsEl) {
      pipsEl.onclick = function (e) {
        var pip = e.target.closest('.river-pip');
        if (!pip) return;
        var idx = parseInt(pip.dataset.pip, 10);
        var newSpeed = SPEED_MIN + (idx / (SPEED_PIPS - 1)) * (SPEED_MAX - SPEED_MIN);
        setSpeed(newSpeed);
      };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PILL RENDERING
  // ═══════════════════════════════════════════════════════════════════════════

  function buildPillFaceHTML(ev) {
    var badge = pillBadge(ev);
    var label = isSpecial(ev)
      ? '<span class="pill-special-text">' + esc(ev.title) + '</span>'
      : '<span class="pill-username">' + esc(ev.actorUsername) + '</span>';

    return '<div class="pill-face">' +
      '<span class="pill-icon">' + ev.icon + '</span>' +
      label +
      (badge ? '<span class="pill-badge">' + esc(badge) + '</span>' : '') +
    '</div>';
  }

  function buildExpandedCardHTML(ev, up) {
    var lifetime = EVENT_LIFETIME[ev.rarity];
    var elapsed = nowMs - ev.createdAt;
    var remaining = Math.max(0, lifetime - elapsed);
    var pct = Math.max(0, Math.min(100, (remaining / lifetime) * 100));
    var lColor = lifetimeColor(pct);
    var isMythic = ev.rarity === 'mythic';

    var headerHtml = '' +
      '<div class="pill-expand-header">' +
        '<div class="pill-avatar">' +
          '<img class="pill-avatar-img" src="' + esc(ev.actorAvatarUrl) + '" alt="" loading="lazy">' +
        '</div>' +
        '<div class="pill-expand-info">' +
          '<div class="pill-expand-user-row">' +
            '<span class="pill-expand-user">' + esc(ev.actorUsername) + '</span>' +
            '<span class="pill-expand-tier">' + esc(ev.actorTier.toUpperCase()) + '</span>' +
          '</div>' +
          '<span class="pill-expand-time">' + timeAgo(ev.createdAt) + '</span>' +
        '</div>' +
      '</div>';

    var actionHtml = '<div class="pill-expand-action">' + ev.icon + ' ' + esc(ev.title) + '</div>';
    var detailHtml = ev.detail ? '<div class="pill-expand-detail">' + esc(ev.detail) + '</div>' : '';

    var sparkHtml = '' +
      '<div class="pill-spark-row">' +
        '<button class="pill-spark-btn' + (ev.sparkedByMe ? ' active' : '') + '" data-spark="' + ev.id + '">' +
          '<svg viewBox="0 0 24 24" fill="' + (ev.sparkedByMe ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>' +
          '<span class="pill-spark-count">' + ev.sparkCount + '</span>' +
        '</button>' +
      '</div>';

    var lifetimeHtml = '' +
      '<div class="pill-lifetime">' +
        '<div class="pill-lifetime-bar" style="width:' + pct + '%;--lifetime-color:' + lColor + ';"></div>' +
        '<div class="pill-lifetime-text">' + formatRemaining(remaining) + ' · ' + RARITY_LABELS[ev.rarity] + '</div>' +
      '</div>';

    var commentsHtml = '';
    if (ev.comments.length > 0) {
      var expanded = (commentsExpandedId === ev.id);
      var shown = expanded ? ev.comments : ev.comments.slice(-2);
      commentsHtml = '<div class="pill-comments' + (expanded ? ' pill-comments-expanded' : '') + '" data-comments-zone="' + ev.id + '">';
      commentsHtml += '<div class="pill-comments-header"><span class="pill-comments-label">' + ev.comments.length + ' comments</span></div>';
      commentsHtml += '<div class="pill-comments-scroll">';
      for (var i = 0; i < shown.length; i++) {
        var c = shown[i];
        commentsHtml += '<div class="pill-comment">' +
          '<img class="pill-comment-avatar" src="' + esc(c.avatarUrl) + '" alt="" loading="lazy">' +
          '<div class="pill-comment-body">' +
            '<span class="pill-comment-user">' + esc(c.username) + '</span>' +
            '<span class="pill-comment-text">' + esc(c.text) + '</span>' +
          '</div>' +
          '<span class="pill-comment-time">' + timeAgo(c.timestamp) + '</span>' +
        '</div>';
      }
      commentsHtml += '</div>';
      commentsHtml += '<div class="pill-comment-input">' +
        '<input class="pill-comment-field" data-comment-input="' + ev.id + '" placeholder="Add a comment…" maxlength="100">' +
        '<button class="pill-comment-send" data-comment-send="' + ev.id + '">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/></svg>' +
        '</button>' +
      '</div>';
      commentsHtml += '</div>';
    }

    var shineHtml = '<div class="pill-expand-shine"></div>';
    var mythicCls = isMythic ? ' pill-expand-mythic' : '';

    if (up) {
      return '<div class="pill-expand-up' + mythicCls + '">' +
        shineHtml + headerHtml + actionHtml + detailHtml + sparkHtml + lifetimeHtml + commentsHtml +
      '</div>';
    } else {
      return '<div class="pill-expand' + mythicCls + '">' +
        shineHtml + headerHtml + actionHtml + detailHtml + sparkHtml + lifetimeHtml + commentsHtml +
      '</div>';
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DOM UPDATE LOOP — Desktop channel
  // ═══════════════════════════════════════════════════════════════════════════

  var pillElements = {};

  function renderDesktopChannel() {
    if (!channelEl) return;
    var t = nowMs;
    var chH = riverHeight;
    var aliveIds = {};

    for (var i = 0; i < activeEvents.length; i++) {
      var ev = activeEvents[i];
      var progress = getProgress(ev, t);
      if (progress < -0.05 || progress > 1.05) continue;
      aliveIds[ev.id] = true;

      var yPos = -40 + progress * (chH + 40);
      var isHovered = (hoveredId === ev.id);

      var trackEl = pillElements[ev.id];
      if (!trackEl) {
        trackEl = document.createElement('div');
        trackEl.className = 'pill-track';
        trackEl.dataset.eventId = String(ev.id);
        trackEl.style.setProperty('--lane', (ev.lane * 100) + '%');
        trackEl.style.setProperty('--depth', String(ev.depth));
        channelEl.appendChild(trackEl);
        pillElements[ev.id] = trackEl;
      }

      trackEl.style.transform = 'translateY(' + yPos.toFixed(1) + 'px)';
      trackEl.style.opacity = isHovered ? '1' : String(Math.min(1, 0.65 + ev.depth * 0.35));

      if (isHovered) {
        trackEl.classList.add('pill-track-paused');
      } else {
        trackEl.classList.remove('pill-track-paused');
      }

      var needsRender = !trackEl._renderedId || trackEl._renderedHovered !== isHovered || trackEl._renderedExpandUp !== expandUp ||
        (isHovered && trackEl._renderedSparkCount !== ev.sparkCount) ||
        (isHovered && trackEl._renderedCommentCount !== ev.comments.length) ||
        (isHovered && trackEl._renderedCommentsExpanded !== (commentsExpandedId === ev.id));

      if (needsRender) {
        var size = pillSize(ev);
        var classes = 'river-pill river-pill-' + size;
        if (isHovered) classes += ' river-pill-hovered';
        if (isHighlight(ev)) classes += ' river-pill-highlight';
        if (isSpecial(ev)) classes += ' river-pill-special';
        if (ev.rarity === 'mythic') classes += ' river-pill-unique';
        if (ev.classInteractive) classes += ' river-pill-class-glow';

        var style = '--wobble-delay:' + (ev.wobblePhase / 6.28).toFixed(2) + 's' +
          ';background:' + rarityBg(ev) +
          ';border-color:' + rarityBorder(ev);

        if (isHovered) {
          style += ';--card-x:' + cardX + 'px';
        }

        var html = '<div class="' + classes + '" data-rarity="' + ev.rarity + '" data-type="' + ev.eventType + '" style="' + style + '">' +
          buildPillFaceHTML(ev);

        if (isHovered) {
          html += buildExpandedCardHTML(ev, expandUp);
        }

        html += '</div>';
        trackEl.innerHTML = html;
        trackEl._renderedId = ev.id;
        trackEl._renderedHovered = isHovered;
        trackEl._renderedExpandUp = expandUp;
        trackEl._renderedSparkCount = ev.sparkCount;
        trackEl._renderedCommentCount = ev.comments.length;
        trackEl._renderedCommentsExpanded = (commentsExpandedId === ev.id);
      }
    }

    var allTrackIds = Object.keys(pillElements);
    for (var j = 0; j < allTrackIds.length; j++) {
      var tid = allTrackIds[j];
      if (!aliveIds[tid]) {
        if (pillElements[tid].parentNode) pillElements[tid].parentNode.removeChild(pillElements[tid]);
        delete pillElements[tid];
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DOM UPDATE — Mobile field
  // ═══════════════════════════════════════════════════════════════════════════

  var mobilePillElements = {};

  function renderMobileField() {
    if (!mobileFieldEl) return;
    var t = nowMs;
    var dm = getDriftMultiplier();
    var aliveIds = {};

    for (var i = 0; i < activeEvents.length; i++) {
      var ev = activeEvents[i];
      var progress = getProgress(ev, t);
      if (progress < -0.05 || progress > 1.05) continue;
      aliveIds[ev.id] = true;

      var trackEl = mobilePillElements[ev.id];
      if (!trackEl) {
        trackEl = document.createElement('div');
        trackEl.className = 'river-mobile-track';
        var mobileLane = [12, 40, 68][Math.floor((ev.lane - LANE_MIN) / (LANE_MAX - LANE_MIN) * 2.99)];
        trackEl.style.setProperty('--mobile-lane', mobileLane + '%');
        trackEl.style.setProperty('--drift-dur', (ev.flowDurationMs * dm / 1000).toFixed(1) + 's');
        trackEl.style.opacity = '1';

        var pillHtml = '<div class="river-mobile-pill" style="border-color:' + rarityBorder(ev) + ';" data-event-id="' + ev.id + '">' +
          '<span class="river-mobile-pill-icon">' + ev.icon + '</span>' +
          '<span class="river-mobile-pill-name">' + esc(ev.actorUsername) + '</span>' +
        '</div>';
        trackEl.innerHTML = pillHtml;
        mobileFieldEl.appendChild(trackEl);
        mobilePillElements[ev.id] = trackEl;

        void trackEl.offsetWidth;
        trackEl.style.animationDelay = (-progress * ev.flowDurationMs * dm / 1000).toFixed(1) + 's';
      }

      var isHovered = (hoveredId === ev.id);
      if (isHovered) {
        trackEl.classList.add('river-mobile-track-paused');
      } else {
        trackEl.classList.remove('river-mobile-track-paused');
      }
    }

    var allIds = Object.keys(mobilePillElements);
    for (var j = 0; j < allIds.length; j++) {
      var tid = allIds[j];
      if (!aliveIds[tid]) {
        if (mobilePillElements[tid].parentNode) mobilePillElements[tid].parentNode.removeChild(mobilePillElements[tid]);
        delete mobilePillElements[tid];
      }
    }
  }

  function renderMobilePopup() {
    var popup = document.getElementById('river-mobile-popup');
    if (!popup) return;
    if (hoveredId == null) { popup.style.display = 'none'; return; }
    var ev = activeEvents.find(function (e) { return e.id === hoveredId; });
    if (!ev) { popup.style.display = 'none'; return; }

    var tc = tierColor(ev.actorTier); // kept for potential future use
    popup.style.display = 'block';
    popup.className = 'river-mobile-popup';
    popup.style.cssText += ';border-color:' + rarityBorder(ev) + ';';

    var html = '<div class="mobile-popup-header">' +
      '<div class="mobile-popup-avatar"><img src="' + esc(ev.actorAvatarUrl) + '" alt=""></div>' +
      '<div class="mobile-popup-info">' +
        '<div class="mobile-popup-user-row">' +
          '<span class="mobile-popup-username">' + esc(ev.actorUsername) + '</span>' +
          '<span class="mobile-popup-tier">' + esc(ev.actorTier.toUpperCase()) + '</span>' +
        '</div>' +
        '<span class="mobile-popup-time">' + timeAgo(ev.createdAt) + '</span>' +
      '</div>' +
      '<span class="mobile-popup-icon">' + ev.icon + '</span>' +
    '</div>' +
    '<div class="mobile-popup-action">' + esc(ev.title) + '</div>' +
    (ev.detail ? '<div class="mobile-popup-detail">' + esc(ev.detail) + '</div>' : '');

    if (ev.comments.length > 0) {
      html += '<div class="mobile-popup-comments"><span class="mobile-popup-comments-label">' + ev.comments.length + ' comments</span>';
      var shown = ev.comments.slice(-3);
      for (var i = 0; i < shown.length; i++) {
        var c = shown[i];
        html += '<div class="mobile-popup-comment">' +
          '<img src="' + esc(c.avatarUrl) + '" alt="">' +
          '<div><span class="mobile-popup-comment-user">' + esc(c.username) + '</span>' +
          '<span class="mobile-popup-comment-text">' + esc(c.text) + '</span></div>' +
        '</div>';
      }
      html += '</div>';
    }

    popup.innerHTML = html;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LAYOUT
  // ═══════════════════════════════════════════════════════════════════════════

  function updateLayout() {
    if (!sidebarEl) return;
    var w = riverCollapsed ? 48 : riverWidth;
    sidebarEl.style.width = w + 'px';
    document.body.style.setProperty('--river-width', w + 'px');

    if (window.innerWidth >= 768) {
      document.body.classList.toggle('river-active', !riverCollapsed);
    } else {
      document.body.classList.remove('river-active');
    }

    var dragHandle = document.getElementById('river-drag-handle');
    var fog1 = sidebarEl.querySelector('.river-depth-fog-top');
    var fog2 = sidebarEl.querySelector('.river-depth-fog-bottom');
    var ambient = sidebarEl.querySelector('.river-ambient');

    if (riverCollapsed) {
      if (channelEl) channelEl.classList.add('river-section-hidden');
      if (dragHandle) dragHandle.style.display = 'none';
      if (fog1) fog1.style.display = 'none';
      if (fog2) fog2.style.display = 'none';
      if (ambient) ambient.style.display = 'none';
    } else {
      if (channelEl) channelEl.classList.remove('river-section-hidden');
      if (dragHandle) dragHandle.style.display = '';
      if (fog1) fog1.style.display = '';
      if (fog2) fog2.style.display = '';
      if (ambient) ambient.style.display = '';
    }

    renderControls();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EVENT HANDLERS
  // ═══════════════════════════════════════════════════════════════════════════

  function handlePillHover(eventId, pillEl) {
    if (hoveredId === eventId) return;
    hoveredId = eventId;
    currentHoldId = eventId;
    currentHoldStart = Date.now();

    if (channelEl) {
      var rect = pillEl.getBoundingClientRect();
      var chRect = channelEl.getBoundingClientRect();
      var bottomSpace = chRect.bottom - rect.bottom;
      expandUp = bottomSpace < 320;
      var pillLeft = rect.left - chRect.left;
      var maxLeft = chRect.width - 290;
      cardX = Math.min(0, maxLeft - pillLeft);
    }

    commentsExpandedId = null;
  }

  function handlePillLeave(eventId) {
    if (hoveredId !== eventId) return;
    if (currentHoldId === eventId && currentHoldStart > 0) {
      var accum = holdAccum.get(eventId) || 0;
      holdAccum.set(eventId, accum + (Date.now() - currentHoldStart));
    }
    currentHoldId = null;
    currentHoldStart = 0;
    hoveredId = null;
    commentsExpandedId = null;
  }

  function setupChannelEvents() {
    if (!channelEl) return;

    channelEl.addEventListener('mouseenter', function (e) {
      var track = e.target.closest('.pill-track');
      if (track) handlePillHover(parseInt(track.dataset.eventId, 10), track);
    }, true);

    channelEl.addEventListener('mouseleave', function (e) {
      var track = e.target.closest('.pill-track');
      if (track) {
        var related = e.relatedTarget;
        if (related && track.contains(related)) return;
        handlePillLeave(parseInt(track.dataset.eventId, 10));
      }
    }, true);

    channelEl.addEventListener('mouseover', function (e) {
      var track = e.target.closest('.pill-track');
      if (track) handlePillHover(parseInt(track.dataset.eventId, 10), track);
    });

    channelEl.addEventListener('mouseout', function (e) {
      var track = e.target.closest('.pill-track');
      if (track) {
        var related = e.relatedTarget;
        if (related && track.contains(related)) return;
        handlePillLeave(parseInt(track.dataset.eventId, 10));
      }
    });

    channelEl.addEventListener('click', function (e) {
      var sparkBtn = e.target.closest('[data-spark]');
      if (sparkBtn) {
        e.stopPropagation();
        sparkEvent(parseInt(sparkBtn.dataset.spark, 10));
        return;
      }
      var sendBtn = e.target.closest('[data-comment-send]');
      if (sendBtn) {
        e.stopPropagation();
        var evId = parseInt(sendBtn.dataset.commentSend, 10);
        var input = channelEl.querySelector('[data-comment-input="' + evId + '"]');
        if (input && input.value.trim()) {
          addComment(evId, input.value);
          input.value = '';
        }
        return;
      }
      var commentsZone = e.target.closest('[data-comments-zone]');
      if (commentsZone) {
        var cId = parseInt(commentsZone.dataset.commentsZone, 10);
        commentsExpandedId = (commentsExpandedId === cId) ? null : cId;
        return;
      }
    });

    channelEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var input = e.target.closest('[data-comment-input]');
        if (input && input.value.trim()) {
          e.preventDefault();
          var evId = parseInt(input.dataset.commentInput, 10);
          addComment(evId, input.value);
          input.value = '';
        }
      }
    });
  }

  function setupMobileEvents() {
    if (!mobileFieldEl) return;

    mobileFieldEl.addEventListener('click', function (e) {
      var pill = e.target.closest('[data-event-id]');
      if (pill) {
        var id = parseInt(pill.dataset.eventId, 10);
        if (hoveredId === id) {
          handlePillLeave(id);
        } else {
          hoveredId = id;
          currentHoldId = id;
          currentHoldStart = Date.now();
          renderMobilePopup();
        }
      }
    });

    document.addEventListener('click', function (e) {
      if (hoveredId != null && !e.target.closest('.river-mobile-field') && !e.target.closest('.river-mobile-popup')) {
        hoveredId = null;
        currentHoldId = null;
        currentHoldStart = 0;
        renderMobilePopup();
      }
    });
  }

  function setupDragHandle() {
    var handle = document.getElementById('river-drag-handle');
    if (!handle) return;

    handle.addEventListener('mousedown', function (e) {
      e.preventDefault();
      handle.classList.add('river-drag-active');
      var startX = e.clientX;
      var startW = riverWidth;

      function onMove(ev) {
        var delta = startX - ev.clientX;
        riverWidth = Math.min(RIVER_WIDTH_MAX, Math.max(RIVER_WIDTH_MIN, startW + delta));
        updateLayout();
      }
      function onUp() {
        handle.classList.remove('river-drag-active');
        savePref('spotter-river-width', riverWidth);
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      }
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // POSITION LOOP — RAF at ~30fps
  // ═══════════════════════════════════════════════════════════════════════════

  function startPositionLoop() {
    var lastWallTime = Date.now();
    var lastFrame = 0;

    function tick(time) {
      if (time - lastFrame >= 33) {
        var wallNow = Date.now();
        var gap = wallNow - lastWallTime;
        lastWallTime = wallNow;

        if (gap > 5000) {
          reseedRiver();
          nowMs = wallNow;
          lastFrame = time;
          requestAnimationFrame(tick);
          return;
        }

        nowMs = wallNow;

        for (var i = activeEvents.length - 1; i >= 0; i--) {
          var ev = activeEvents[i];
          var progress = getProgress(ev, nowMs);
          if (progress > 1.05 || nowMs > ev.expiresAt) {
            holdAccum.delete(ev.id);
            markEventSeen(ev.id);
          }
        }

        if (!riverCollapsed) {
          renderDesktopChannel();
        }
        renderMobileField();
        if (hoveredId != null && window.innerWidth < 768) {
          renderMobilePopup();
        }

        lastFrame = time;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════════════════

  function init() {
    sidebarEl = document.getElementById('river-sidebar');
    if (!sidebarEl) return;

    sidebarEl.innerHTML = buildSidebarHTML();
    channelEl = document.getElementById('river-channel');

    var mobileEl = document.getElementById('river-mobile');
    if (mobileEl) {
      mobileEl.innerHTML = buildMobileHTML();
      mobileFieldEl = document.getElementById('river-mobile-field');
      mobilePopupEl = document.getElementById('river-mobile-popup');
    }

    if (channelEl) {
      riverHeight = channelEl.clientHeight || 700;
      var ro = new ResizeObserver(function () {
        riverHeight = channelEl.clientHeight || 700;
      });
      ro.observe(channelEl);
    }

    updateLayout();
    setupChannelEvents();
    setupMobileEvents();
    setupDragHandle();

    startMockGenerator();
    startPositionLoop();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
