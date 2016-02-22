"""Protocol classes"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


# TODO: maybe find a better name ? -> sweep ?


class Protocol(object):

    """Stimulus protocol"""

    def __init__(self, name=None, stimuli=None, recordings=None):
        """Constructor"""
        self.name = name
        self.stimuli = stimuli
        self.recordings = recordings

    @property
    def total_duration(self):
        """Total duration"""

        return max([stimulus.total_duration for stimulus in self.stimuli])

    @property
    def responses(self):
        """Return all the responses"""
        return {
            recording.name: recording.response for recording in self.recordings}

    def instantiate(self, cell):
        """Instantiate protocol"""

        for stimulus in self.stimuli:
            stimulus.instantiate(cell)

        for recording in self.recordings:
            recording.instantiate(cell)

    def destroy(self):
        """Destroy protocol"""

        for stimulus in self.stimuli:
            stimulus.destroy()

        for recording in self.recordings:
            recording.destroy()

    def __str__(self):
        """String representation"""

        content = '%s:\n' % self.name

        content += '  stimuli:\n'
        for stimulus in self.stimuli:
            content += '    %s\n' % str(stimulus)

        content += '  recordings:\n'
        for recording in self.recordings:
            content += '    %s\n' % str(recording)

        return content
