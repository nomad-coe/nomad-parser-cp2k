package eu.nomad_lab.parsers

import eu.{ nomad_lab => lab }
import eu.nomad_lab.DefaultPythonInterpreter
import org.{ json4s => jn }
import scala.collection.breakOut

object Cp2kParser extends SimpleExternalParserGenerator(
  name = "Cp2kParser",
  parserInfo = jn.JObject(
    ("name" -> jn.JString("Cp2kParser")) ::
      ("parserId" -> jn.JString("Cp2kParser" + lab.Cp2kVersionInfo.version)) ::
      ("versionInfo" -> jn.JObject(
        ("nomadCoreVersion" -> jn.JString(lab.NomadCoreVersionInfo.version)) ::
          (lab.Cp2kVersionInfo.toMap.map {
            case (key, value) =>
              (key -> jn.JString(value.toString))
          }(breakOut): List[(String, jn.JString)])
      )) :: Nil
  ),
  mainFileTypes = Seq("text/.*"),
  mainFileRe = """  \*\*\*\* \*\*\*\* \*\*\*\*\*\*  \*\*  PROGRAM STARTED AT\s(?<cp2kStartedAt>.*)
 \*\*\*\*\* \*\* \*\*\*  \*\*\* \*\*   PROGRAM STARTED ON\s*.*
 \*\*    \*\*\*\*   \*\*\*\*\*\*    PROGRAM STARTED BY .*
 \*\*\*\*\* \*\*    \*\* \*\* \*\*   PROGRAM PROCESS ID .*
  \*\*\*\* \*\*  \*\*\*\*\*\*\*  \*\*  PROGRAM STARTED IN .*
(?:\s*\n|                                      \s+.*
)*
(?:\s*CP2K\| version string:\s*(?<cp2kVersionString>.*)
)?(?:\s*CP2K\| source code revision number:\s*(?<cp2kRevision>.*)
)?""".r,
  cmd = Seq(DefaultPythonInterpreter.python2Exe(), "${envDir}/parsers/cp2k/parser/parser-cp2k/cp2kparser/scalainterface.py",
    "--uri", "${mainFileUri}", "${mainFilePath}"),
  cmdCwd = "${mainFilePath}/..",
  resList = Seq(
    "parser-cp2k/cp2kparser/utils/baseclasses.py",
    "parser-cp2k/cp2kparser/utils/testing.py",
    "parser-cp2k/cp2kparser/utils/__init__.py",
    "parser-cp2k/cp2kparser/utils/logconfig.py",
    "parser-cp2k/cp2kparser/__init__.py",
    "parser-cp2k/cp2kparser/parsing/versions/__init__.py",
    "parser-cp2k/cp2kparser/parsing/versions/cp2k262/inputparsing.py",
    "parser-cp2k/cp2kparser/parsing/versions/cp2k262/__init__.py",
    "parser-cp2k/cp2kparser/parsing/versions/cp2k262/implementation.py",
    "parser-cp2k/cp2kparser/parsing/versions/cp2k262/outputparser.py",
    "parser-cp2k/cp2kparser/parsing/versions/versionsetup.py",
    "parser-cp2k/cp2kparser/parsing/__init__.py",
    "parser-cp2k/cp2kparser/parsing/cp2kinputenginedata/xmlpreparser.py",
    "parser-cp2k/cp2kparser/parsing/cp2kinputenginedata/__init__.py",
    "parser-cp2k/cp2kparser/parsing/cp2kinputenginedata/input_tree.py",
    "parser-cp2k/cp2kparser/parsing/parser.py",
    "parser-cp2k/cp2kparser/parsing/csvparsing.py",
    "parser-cp2k/cp2kparser/setup_paths.py",
    "parser-cp2k/cp2kparser/scalainterface.py",
    "nomad_meta_info/public.nomadmetainfo.json",
    "nomad_meta_info/common.nomadmetainfo.json",
    "nomad_meta_info/meta_types.nomadmetainfo.json",
    "nomad_meta_info/cp2k.nomadmetainfo.json"
  ) ++ DefaultPythonInterpreter.commonFiles(),
  dirMap = Map(
    "parser-cp2k" -> "parsers/cp2k/parser/parser-cp2k",
    "nomad_meta_info" -> "nomad-meta-info/meta_info/nomad_meta_info"
  ) ++ DefaultPythonInterpreter.commonDirMapping()
)
