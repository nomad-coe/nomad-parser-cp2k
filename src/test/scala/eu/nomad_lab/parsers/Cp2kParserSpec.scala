package eu.nomad_lab.parsers

import org.specs2.mutable.Specification

object Cp2kParserSpec extends Specification {
  "Cp2kParserTest" >> {
    "test with json-events" >> {
      ParserRun.parse(Cp2kParser, "parsers/cp2k/test/examples/energy_force/si_bulk8.out", "json-events") must_== ParseResult.ParseSuccess
    }
  }

  "test energy_force with json" >> {
    ParserRun.parse(Cp2kParser, "parsers/cp2k/test/examples/energy_force/si_bulk8.out", "json") must_== ParseResult.ParseSuccess
  }
  "test geo_opt with json" >> {
    ParserRun.parse(Cp2kParser, "parsers/cp2k/test/examples/geo_opt/H2O.out", "json") must_== ParseResult.ParseSuccess
  }
}
