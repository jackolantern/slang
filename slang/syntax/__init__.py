class Position:
    def __init__(self, rule, start_line, end_line, start_position, end_position):
        self.rule = rule
        self.end_line = end_line
        self.start_line = start_line
        self.end_position = end_position
        self.start_position = start_position

    @classmethod
    def from_parseinfo(cls, info):
        return cls(info.rule, info.line, info.endline, info.pos, info.endpos)

    def __repr__(self):
        return (
            f"Position({self.rule},"
            f"end_line={self.end_line},"
            f"start_line={self.start_line},"
            f"end_position={self.end_position},"
            f"start_position={self.start_position})"
        )
