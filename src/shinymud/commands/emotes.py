"""The emotes are grouped in the following structure:
'emote_name': (['actor view, no target',
                'room view, no target'
               ],
               ['actor view, with target',
                'target view',
                'room view, with target'
               ]
              )
"""
EMOTES = {  'slap': (['You stand around looking for someone to slap.',
                      '#actor looks like #a_she/he\'s going to slap someone.'
                     ], 
                     ['You slap #target.',
                      '#actor slaps you.',
                      '#actor slaps #target.'
                     ]
                    ),
            'wave': (['You wave.', 
                      '#actor waves.'
                     ],
                     ['You wave to #target.', 
                      '#actor waves to you.', 
                      '#actor waves to #target.'
                     ]
                    ),
            'explode': (['You explode into thousands of bloody chunks!',
                         '#actor explodes into thousands of bloody chunks!'
                        ],
                        ['You explode on #target, getting bloody chunks all over #t_her/him!',
                         '#actor explodes, covering you in bloody chunks!',
                         '#actor explodes all over #target. Eww.'
                        ]
                       ),
            'fall': (['You face plant into the floor.', 
                      '#actor looses #a_her/his balance and face plants into the floor.'
                     ],
                     ['You fall on #target.', 
                      '#actor falls on you.', 
                      '#actor falls on #target.'
                     ]
                    ),
            'laugh': (['You laugh.', '#actor laughs.'], []),
            'giggle': (['You giggle.', '#actor giggles.'], []),
            'hattip': (['You gallantly tip your hat to the room.',
                        '#actor gallantly tips #a_her/his hat to the room.'
                       ],
                       ['You gallantly tip your hat to #target.',
                        '#actor gallantly tips #a_her/his hat to you.', 
                        '#actor gallantly tips #a_her/his hat to #target.'
                       ],
                      ),
            'eyebrow': (['You raise an eyebrow.', '#actor raises an eyebrow.'
                      ],
                      ['You raise an eyebrow at #target.',
                       '#actor raises an eyebrow at you.',
                       '#actor raises an eyebrow at #target.'
                      ]),
            'sigh': (['You sigh.', '#actor sighs.'], []),
            'pet': (['You pet yourself.','#actor pets #t_self.'], 
                    ['You pet #target.',
                     '#actor pets you.',
                     '#actor pets #target.'
                    ]),
            'purr': (['You purr contentedly.', '#actor purrs contentedly.'], []),
            'grr': (['You growl in frustration.',
                     '#actor growls in frustration.'
                    ],
                    ['You growl at #target.',
                     '#actor growls at you.',
                     '#actor growls at #target.'
                    ])
         }
