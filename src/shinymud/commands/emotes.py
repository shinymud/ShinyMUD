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
                      '#actor lookes like #a_she/he\'s going to slap someone.'
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
                         '#actor expodes into thousands of bloody chunks!'
                        ],
                        ['You explode on #target, getting bloody chunks all over #t_her/him!',
                         '#actor explodes, covoring you in bloody chunks!',
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
            'eyebrow': (['You raise an eyebrow.', '#actor raises an eybrow.'
                      ],
                      ['You raise an eyebrow at #target.',
                       '#actor raises an eyebrow at you.',
                       '#actor raises an eyebrow at #target.'
                      ])
         }
