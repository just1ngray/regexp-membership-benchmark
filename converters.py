from FAdo.reex import *


class RegExpConverter:
    """This class defines methods that can be overridden and re-implemented to support the
    different conversions of `string <--> sre <--> regexp`

    String: good for serialization
    SRE:    more compact and can take advantage of pairwise language generation optimizations
    RegExp: full FAdo implementation
    """

    @classmethod
    def str_to_regexp(cls, string: str, sigma=None) -> RegExp:
        """Convert a string into a standard RegExp with binary compositions"""
        return str2regexp(string, sigma=sigma)

    @classmethod
    def str_to_sre(cls, string: str, sigma=None) -> RegExp:
        """Convert a string into a special RegExp with higher dimensionality"""
        return str2sre(string, sigma=sigma)

    @classmethod
    def regexp_to_sre(cls, regexp: RegExp) -> RegExp:
        """Convert a binary RegExp into special version"""
        return to_s(regexp)

    @classmethod
    def sre_to_regexp(cls, sre: RegExp) -> RegExp:
        """Convert a SRE into a standard FAdo RegExp.
        Why? Because FAdo has better implementations for standard RegExp's than the SRE type.

        For every regular expression E: `sre_to_regexp(str2sre(E)).equivP(str2regexp(E))`
        """
        def sconcat(re):
            if len(re.arg) == 2:
                return CConcat(RegExpConverter.sre_to_regexp(re.arg[0]), RegExpConverter.sre_to_regexp(re.arg[1]),
                                sre.Sigma)
            elif len(re.arg) == 3:
                return CConcat(RegExpConverter.sre_to_regexp(re.arg[0]), CConcat(RegExpConverter.sre_to_regexp(re.arg[1]),
                            RegExpConverter.sre_to_regexp(re.arg[2]), sre.Sigma), sre.Sigma)
            else:
                h = len(re.arg) // 2
                return CConcat(RegExpConverter.sre_to_regexp(SConcat(re.arg[:h], sre.Sigma)),
                        RegExpConverter.sre_to_regexp(SConcat(re.arg[h:], sre.Sigma)), sre.Sigma)

        def sdisj(re):
            arg = list(re.arg)
            if len(arg) == 2:
                return CDisj(RegExpConverter.sre_to_regexp(arg[0]), RegExpConverter.sre_to_regexp(arg[1]),
                            sre.Sigma)
            elif len(arg) == 3:
                return CDisj(RegExpConverter.sre_to_regexp(arg[0]), CDisj(RegExpConverter.sre_to_regexp(arg[1]),
                            RegExpConverter.sre_to_regexp(arg[2]), sre.Sigma), sre.Sigma)
            else:
                h = len(arg) // 2
                return CDisj(RegExpConverter.sre_to_regexp(SDisj(arg[:h], sre.Sigma)),
                        RegExpConverter.sre_to_regexp(SDisj(arg[h:], sre.Sigma)), sre.Sigma)

        return {
            # base cases
            CAtom:      lambda: sre,
            CEpsilon:   lambda: sre,
            CEmptySet:  lambda: sre,

            # "C" composite cases
            CConcat:    lambda: CConcat(RegExpConverter.sre_to_regexp(sre.arg1),
                                        RegExpConverter.sre_to_regexp(sre.arg2), sre.Sigma),
            CDisj:      lambda: CDisj(RegExpConverter.sre_to_regexp(sre.arg1),
                                        RegExpConverter.sre_to_regexp(sre.arg2), sre.Sigma),
            CStar:      lambda: CStar(RegExpConverter.sre_to_regexp(sre.arg), sre.Sigma),

            # "S" composite cases
            SConcat:    lambda: sconcat(sre),
            SDisj:      lambda: sdisj(sre),
            SStar:      lambda: CStar(RegExpConverter.sre_to_regexp(sre.arg), sre.Sigma),
        }[type(sre)]()
